"""Actual DEX/APK controls from two independent local component branches.

These artifacts are never signed, installed, or approved as product updates.
Both branches start at the same source. Only their own runtime version method
changes. The combiner must preserve the newer opposite owner byte-for-byte.
"""
import argparse,copy,json,shutil,subprocess
from pathlib import Path
from zipfile import ZipFile
from inventory import HERE,ROOT,APP,PACKAGE,CERT_SHA,load,save,canonical,digest,file_sha
from component_bundles import OWNED,read_bundle,record,combine
from release_gate import component_digest,inspect_candidate,Rejected,require
from release_authority import guarded,validate,verify,transition

def run(args,**kw):return subprocess.check_output(list(map(str,args)),text=True,**kw).strip()

def authority(catalog,metas,version=2103421,generation=2):
    payload={k:v for m in metas.values() for k,v in m['payload'].items()}
    return {'schema':2,'status':'ENGINEERING_REVIEWED_FOLD_PENDING','generation':generation,
      'package':PACKAGE,'certificate_sha256':CERT_SHA,'last_issued_versionCode':2103420,
      'candidate_versionCode':version,'accepted_registry_sha256':file_sha(HERE/'accepted-combined-release.json'),
      'accepted_pointer_updated':False,'release_blockers':[], 'payload':payload,
      'components':{o:{k:metas[o][k] for k in ('version','settings_schema','approved_source','digest')}|{'revision':1} for o in OWNED},
      'protected_contract':{k:v['sha256'] for k,v in payload.items() if guarded(k)}}

def update_bundle(owner,base_catalog,bundles,out,source,jars,android,d8):
    folder=out/owner;tree=folder/'branch'
    branch='test/isolation-combination-'+owner.lower()+'-'+source[:10]
    # A harness-only failure can resume already built, unsigned controls.
    # Recheck their exact branch diff and every packaged class first.
    if folder.exists():
        short='Infinity' if owner=='INFINITY' else 'Cobra';name=short+'Component'
        branch_source=run(['git','-C',tree,'rev-parse','HEAD'])
        changed=run(['git','-C',tree,'diff','--name-only',source,branch_source]).splitlines()
        require(changed==[str(HERE.relative_to(ROOT)/'runtime'/(name+'.java'))],'RESUME_BRANCH_SCOPE')
        path=bundles/(owner+'-control.zip')
        with ZipFile(path) as z:meta=json.loads(z.read('component.json'))
        expected={k:meta[k] for k in ('version','digest','approved_source','settings_schema')}
        expected.update(file=path.name,sha256=file_sha(path));read_bundle(path,expected)
        old=read_bundle(bundles/base_catalog['bundles'][owner]['file'],base_catalog['bundles'][owner])
        delta=[k for k in meta['payload'] if meta['payload'][k]!=old['payload'].get(k)]
        require(set(meta['payload'])==set(old['payload']) and delta==['class:'+APP+name+';'],'RESUME_PAYLOAD_SCOPE')
        require(meta['approved_source']==branch_source,'RESUME_SOURCE')
        return expected,meta,{'branch':branch,'source':branch_source,'base':source,'changed_classes':delta,
            'other_class_definitions_exact':sum(k.startswith('class:') for k in meta['payload'])-1,
            'opposite_owner_dex_used_in_component_build':False}
    folder.mkdir()
    run(['git','-C',ROOT,'worktree','add','-b',branch,tree,source])
    short='Infinity' if owner=='INFINITY' else 'Cobra';name=short+'Component'
    java=tree/HERE.relative_to(ROOT)/'runtime'/(name+'.java')
    old=base_catalog['bundles'][owner]['version'];new=old+'.control2'
    java.write_text(java.read_text().replace('"'+old+'"','"'+new+'"'))
    run(['git','-C',tree,'add',java]);run(['git','-C',tree,'commit','-m','Unsigned isolation control: '+owner+' version method only'])
    branch_source=run(['git','-C',tree,'rev-parse','HEAD'])
    compiled=folder/'classes';compiled.mkdir()
    run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options','-d',compiled,java])
    dex=folder/'patch';dex.mkdir()
    run(['java','-cp',d8,'com.android.tools.r8.D8','--min-api','21','--lib',android,'--output',dex,
         compiled/'com/projectinfinity/kodi'/(name+'.class')])
    row=base_catalog['bundles'][owner];meta=read_bundle(bundles/row['file'],row)
    originals=folder/'originals';originals.mkdir()
    with ZipFile(bundles/row['file']) as z:
        for n in meta['dex']:(originals/Path(n).name).write_bytes(z.read(n))
    assignments=folder/'assignments.tsv';assignments.write_text(''.join(k[6:]+'\t'+owner+'\n' for k in sorted(meta['payload']) if k.startswith('class:')))
    origin=folder/'origins.tsv';origin.write_text(APP+name+';\t'+APP+name+';\n')
    cp=':'.join(map(str,sorted(jars.glob('*.jar'))));host=folder/'host';host.mkdir()
    run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options',
         '-cp',cp,'-d',host,HERE/'ModuleDexWriter.java'])
    run(['java','-cp',str(host)+':'+cp,'org.jf.dexlib2.writer.pool.ModuleDexWriter',folder/'owner-dex',assignments,origin,dex/'classes.dex','-',*sorted(originals.glob('*.dex'))])
    actual={};new_dex={}
    for p in sorted((folder/'owner-dex'/owner).glob('*.dex')):
        smali=p.with_suffix('');run(['java','-cp',str(jars/'*'),'org.jf.baksmali.Main','disassemble','--sequential-labels',p,'-o',smali])
        new_dex['dex/'+p.name]=file_sha(p)
        for s in smali.rglob('*.smali'):actual['class:'+s.read_text().splitlines()[0].split()[-1]]=file_sha(s)
    old_classes={k:v['sha256'] for k,v in meta['payload'].items() if k.startswith('class:')}
    require(set(actual)==set(old_classes),'CONTROL_CHANGED_CLASS_SET')
    changed=[k for k in actual if actual[k]!=old_classes[k]]
    require(changed==['class:'+APP+name+';'],'CONTROL_CHANGED_NON_TARGET_METHOD')
    revised=copy.deepcopy(meta);revised.update(version=new,approved_source=branch_source,dex=new_dex)
    for k,sha in actual.items():revised['payload'][k]['sha256']=sha
    revised['digest']=component_digest(revised['payload'],owner)
    path=bundles/(owner+'-control.zip')
    with ZipFile(bundles/row['file']) as old_zip,ZipFile(path,'w') as z:
        for n in revised['members']:z.writestr(record('payload/'+n),old_zip.read('payload/'+n))
        for n in new_dex:z.writestr(record(n),(folder/'owner-dex'/owner/Path(n).name).read_bytes())
        z.writestr(record('component.json'),canonical(revised))
    result={k:revised[k] for k in ('version','digest','approved_source','settings_schema')}
    result.update(file=path.name,sha256=file_sha(path))
    return result,revised,{'branch':branch,'source':branch_source,'base':source,'changed_classes':changed,
                           'other_class_definitions_exact':len(actual)-1,'opposite_owner_dex_used_in_component_build':False}

def check(bundles,out,jars,android,d8):
    out.mkdir(exist_ok=True);base=load(bundles/'catalog.json');source=base['source']
    metas={o:read_bundle(bundles/r['file'],r) for o,r in base['bundles'].items()}
    original=authority(base,metas);validate(original)
    builds={};updates={};new_metas={}
    for owner in ('INFINITY','COBRA'):
        updates[owner],new_metas[owner],builds[owner]=update_bundle(owner,base,bundles,out,source,jars,android,d8)
    first=copy.deepcopy(base);first['bundles']['INFINITY']=updates['INFINITY']
    second=copy.deepcopy(first);second['bundles']['COBRA']=updates['COBRA']
    a=authority(first,metas|{'INFINITY':new_metas['INFINITY']},2103422,3);a['components']['INFINITY']['revision']=2
    b=authority(second,metas|new_metas,2103423,4)
    for o in ('INFINITY','COBRA'):b['components'][o]['revision']=2
    transition(original,a,{'INFINITY'});transition(a,b,{'COBRA'})
    results=[]
    def build(label,catalog,version,expected,reject=None):
        apk=out/(label+'.apk')
        if not apk.exists():combine(bundles,catalog,apk,version)
        audit=out/(label+'-dex')
        while audit.exists():audit=Path(str(audit)+'-recheck')
        actual,read_version=inspect_candidate(apk,jars,audit)
        require(read_version==version,'VERSION_INSPECTION')
        try:verify(expected,actual,version,expected['generation'])
        except Rejected as e:
            if reject is None or reject not in str(e):raise
            decision='REJECTED:'+str(e)
        else:
            require(reject is None,'STALE_APK_ACCEPTED');decision='ACCEPTED_UNSIGNED_CONTROL'
        results.append({'case':label,'apk_sha256':file_sha(apk),'versionCode':version,'decision':decision,
                        'actual_class_and_member_count':len(actual)})
        return apk,actual
    build('infinity_new_cobra_preserved',first,2103422,a)
    apk,actual=build('both_independently_updated',second,2103423,b)
    stale_i=copy.deepcopy(second);stale_i['bundles']['INFINITY']=base['bundles']['INFINITY']
    stale_c=copy.deepcopy(second);stale_c['bundles']['COBRA']=base['bundles']['COBRA']
    reserved=copy.deepcopy(b);reserved['candidate_versionCode']=2103424
    build('higher_app_stale_infinity',stale_i,2103424,reserved,'STALE_OR_MUTATED_OWNER:INFINITY')
    build('higher_app_stale_cobra',stale_c,2103424,reserved,'STALE_OR_MUTATED_OWNER:COBRA')
    # Actual unexpected common-manifest change; version alone is still valid.
    changed=out/'unexpected-common-manifest.apk'
    with ZipFile(apk) as z,ZipFile(changed,'w') as target:
        for info in z.infolist():
            raw=z.read(info)
            if info.filename=='AndroidManifest.xml':
                encoding='utf-8' if b'CobraBackgroundService' in raw else 'utf-16le'
                needle='CobraBackgroundService'.encode(encoding);require(raw.count(needle)==1,'MANIFEST_CONTROL_LOCATOR')
                raw=raw.replace(needle,'CobraBackgroundServicX'.encode(encoding))
            target.writestr(info,raw)
    audit=out/'unexpected-common-manifest-dex'
    while audit.exists():audit=Path(str(audit)+'-recheck')
    actual_bad,version=inspect_candidate(changed,jars,audit)
    try:verify(b,actual_bad,version,4)
    except Rejected as e:
        require('STALE_OR_MUTATED_OWNER:MINIMAL_ANDROID_CONTRACT' in str(e),'WRONG_COMMON_REJECTION')
        results.append({'case':'unexpected-common-manifest','apk_sha256':file_sha(changed),'decision':'REJECTED:'+str(e)})
    else:raise AssertionError('Mutated common manifest accepted')
    # Actual independently built other-owner code cannot ride an owner-only proposal.
    for target,forbidden in [('COBRA','INFINITY'),('INFINITY','COBRA')]:
        proposed=copy.deepcopy(b);proposed['generation']=3
        try:transition(original,proposed,{target})
        except Rejected as e:
            require('CROSS_OWNER_MUTATION:'+forbidden in str(e),'WRONG_OWNER_REJECTION')
            results.append({'case':target.lower()+'-only-cross-owner-code','decision':'REJECTED:'+str(e)})
        else:raise AssertionError('Cross-owner update accepted')
    # Even a coordinated digest/label change cannot silently rewrite a protected receipt callback.
    for key in [k for k in b['protected_contract'] if any(n in k for n in ('CobraJavaWriteBarrier;','InfinityCloseGuardService;'))]:
        proposed=copy.deepcopy(b);proposed['generation']=a['generation']+1
        proposed['payload'][key]['sha256']=digest(b'unapproved lifecycle callback')
        owner=proposed['payload'][key]['owner'];proposed['components'][owner]['digest']=component_digest(proposed['payload'],owner)
        proposed['protected_contract'][key]=proposed['payload'][key]['sha256']
        try:transition(a,proposed,{'COBRA'})
        except Rejected as e:
            require('SEPARATE_LIFECYCLE_AUTHORIZATION_REQUIRED' in str(e),'WRONG_CONTRACT_REJECTION')
            results.append({'case':'protected-callback:'+key,'decision':'REJECTED:'+str(e)})
        else:raise AssertionError('Protected contract update accepted')
    save(out/'COMBINATION-CONTROLS.json',{'status':'PASS_ACTUAL_INDEPENDENT_COMPONENT_MATRIX','base_source':source,
       'component_builds':builds,'cases':results,'production_catalog_sha256':file_sha(bundles/'catalog.json'),
       'source_inputs':{p.name:file_sha(p) for p in [HERE/'test_component_matrix.py',HERE/'release_authority.py',HERE/'component_bundles.py',HERE/'ModuleDexWriter.java']},
       'control_artifacts_signed':False,'application_executed':False,'accepted_pointer_updated':False})

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('bundles','out','jars','android','d8'):p.add_argument('--'+n,type=Path,required=True)
    check(**vars(p.parse_args()))
