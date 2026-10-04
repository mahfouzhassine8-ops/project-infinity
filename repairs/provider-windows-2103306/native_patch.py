#!/usr/bin/env python3
"""Preserve provider-owned WindowXML coordinates over the exact 3305 lineage.

This is not a provider rewrite, a Back cancellation workaround, or a crash fix.
Only a provider fallback lookup opts out; active-skin overrides stay adaptive.
"""
import argparse
import hashlib
import json
from pathlib import Path

FILES = ('xbmc/addons/Skin.h', 'xbmc/addons/Skin.cpp',
         'xbmc/interfaces/legacy/WindowXML.cpp')
PARENT_PROOF_SHA256 = 'b870052cc344b8d419ed8fb29eb5dbc019fdbc9a528219a576576dcc4332b82b'
PARENT_SOURCE_MAP_SHA256 = 'dc3cd4dce5abcfe7bb4b4a316a8b6a3ce9f69f308546ffe721e4d7b6787ebd1c'
LOCKED_PREIMAGES = {
    FILES[0]: '4933bc3796dd39bbe8e7f5c62d3ba7c4301dcecf74866f9764853b09d9f7cffa',
    FILES[1]: 'fd14e91acfd0d95639010f2c3fd9f3746982b58eb53e65592499d9cba055f6c3',
    FILES[2]: 'ff2596e7eb1e14fde3048859b09be1ef4914ed8e89dba26f6fc9078741e256df',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Unreviewed native preimage: ' + old[:100])
    return text.replace(old, new, 1)


def transform(name, text):
    if name == FILES[0]:
        text = once(text,
            '   \\param baseDir [in] If non-empty, the given directory is searched instead of the skin\'s directory.  Defaults to empty.',
            '   \\param baseDir [in] If non-empty, the given directory is searched instead of the skin\'s directory.  Defaults to empty.\n'
            '   \\param adaptWindow [in] False for provider-owned fallback XML: preserve its declared coordinates.')
        return once(text, '  std::string GetSkinPath(const std::string& file,\n'
                    '                          RESOLUTION_INFO* res = nullptr,\n'
                    '                          const std::string& baseDir = "") const;',
                    '  std::string GetSkinPath(const std::string& file,\n'
                    '                          RESOLUTION_INFO* res = nullptr,\n'
                    '                          const std::string& baseDir = "",\n'
                    '                          bool adaptWindow = true) const;')
    if name == FILES[1]:
        if 'bool CSkinInfo::UsesNativeWindowAdaptation() const' not in text:
            raise ValueError('Missing inherited in-place responsive lineage')
        text = once(text,
            'std::string CSkinInfo::GetSkinPath(const std::string& strFile, RESOLUTION_INFO *res, const std::string& strBaseDir /* = "" */) const',
            'std::string CSkinInfo::GetSkinPath(const std::string& strFile, RESOLUTION_INFO *res,\n'
            '                                  const std::string& strBaseDir /* = "" */,\n'
            '                                  bool adaptWindow /* = true */) const')
        start = text.index('std::string CSkinInfo::GetSkinPath(')
        end = text.index('\nbool CSkinInfo::HasSkinFile(', start)
        method = text[start:end]
        method = once(method, '  if (UsesNativeResponsiveLayout())',
                      '  // INFINITY_PROVIDER_COORDS_V1: a fallback XML owns its declared canvas.\n'
                      '  if (adaptWindow && UsesNativeResponsiveLayout())')
        if method.count('if (UsesNativeWindowAdaptation())') != 2:
            raise ValueError('Unreviewed adaptive resolver branches')
        method = method.replace('if (UsesNativeWindowAdaptation())',
                                'if (adaptWindow && UsesNativeWindowAdaptation())')
        return text[:start] + method + text[end:]
    if name != FILES[2]:
        raise ValueError('Unexpected native target: ' + name)
    text = once(text, '#include "utils/URIUtils.h"',
                '#include "utils/URIUtils.h"\n#include "utils/log.h"')
    text = once(text, '      RESOLUTION_INFO res;\n',
                '      RESOLUTION_INFO res;\n      bool providerOwned = false;\n')
    text = once(text, '        std::string str("none");',
                '        // INFINITY_PROVIDER_COORDS_V1: do not apply the active skin canvas\n'
                '        // to provider XML with its own fixed coordinate contract.\n'
                '        providerOwned = true;\n        std::string str("none");')
    text = once(text, 'g_SkinInfo->GetSkinPath(xmlFilename, &res, basePath);',
                'g_SkinInfo->GetSkinPath(xmlFilename, &res, basePath, false);')
    # Never seed a provider skin from a prior failed active-skin lookup.
    if text.count('std::make_shared<ADDON::CSkinInfo>(addonInfo, res);') != 2:
        raise ValueError('Unreviewed fallback constructors')
    text = text.replace('std::make_shared<ADDON::CSkinInfo>(addonInfo, res);',
                        'std::make_shared<ADDON::CSkinInfo>(addonInfo, declaredRes);')
    text = once(text, '        ADDON::CSkinInfo::TranslateResolution(defaultRes, res);',
                '        RESOLUTION_INFO declaredRes;\n'
                '        ADDON::CSkinInfo::TranslateResolution(defaultRes, declaredRes);')
    if text.count('skinInfo->GetSkinPath(xmlFilename, &res);') != 2:
        raise ValueError('Unreviewed provider lookup count')
    text = text.replace('skinInfo->GetSkinPath(xmlFilename, &res);',
                        'skinInfo->GetSkinPath(xmlFilename, &res, "", false);')
    text = once(text, '      interceptor->SetCoordsRes(res);',
                '      interceptor->SetCoordsRes(res);\n'
                '      interceptor->SetProperty("Infinity.ProviderOwned", providerOwned);\n'
                '      interceptor->SetProperty("Infinity.ProviderXML", xmlFilename);\n'
                '      interceptor->SetProperty("Infinity.ProviderLogicalWidth", res.iWidth);\n'
                '      interceptor->SetProperty("Infinity.ProviderLogicalHeight", res.iHeight);\n'
                '      CLog::Log(LOGINFO, "Infinity provider window: id={} xml={} provider_owned={} "\n'
                '                "logical={}x{} active_skin={}", interceptor->GetID(), xmlFilename,\n'
                '                providerOwned, res.iWidth, res.iHeight, g_SkinInfo->ID());')
    return once(text, '    bool WindowXML::OnAction(const CAction &action)\n    {\n      XBMC_TRACE;',
                '    bool WindowXML::OnAction(const CAction &action)\n    {\n      XBMC_TRACE;\n'
                '      if (action.GetID() == ACTION_NAV_BACK || action.GetID() == ACTION_PREVIOUS_MENU)\n'
                '        CLog::Log(LOGINFO, "Infinity provider Back queued: id={} action={} xml={}",\n'
                '                  interceptor->GetID(), action.GetID(),\n'
                '                  interceptor->GetProperty("Infinity.ProviderXML").asString());')


def snapshot(root):
    return {p.relative_to(root).as_posix(): digest(p.read_bytes())
            for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['apply', 'verify'])
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--parent-proof', type=Path)
    args = parser.parse_args()
    if args.command == 'apply':
        if args.parent_proof is None:
            parser.error('apply requires exact 3304 engine --parent-proof (3305 native is byte-identical)')
        parent = json.loads(args.parent_proof.read_text())
        # Filesystem enumeration/JSON formatting can vary across CI runners.
        # Guard all 9,372 exact pathname->byte-hash pairs, not incidental order.
        source_map = json.dumps(parent['after'], sort_keys=True, separators=(',', ':')).encode()
        if len(parent['after']) != 9372 or digest(source_map) != PARENT_SOURCE_MAP_SHA256:
            raise ValueError('Locked 3305 complete native source map differs')
        before = snapshot(args.source)
        for name, h in LOCKED_PREIMAGES.items():
            if before.get(name) != h:
                raise ValueError('Locked APK 2103305 native preimage mismatch: ' + name)
        mismatches = [n for n, h in parent['after'].items() if before.get(n) != h]
        if mismatches:
            raise ValueError('Native parent proof mismatch: ' + str(mismatches[:20]))
        # Validate every preimage before writing any source file.
        results = {n: transform(n, (args.source / n).read_text()).encode() for n in FILES}
        for n, payload in results.items():
            (args.source / n).write_bytes(payload)
        after = snapshot(args.source)
        changed = {n for n in before.keys() | after.keys() if before.get(n) != after.get(n)}
        if changed != set(FILES):
            raise ValueError('Unexpected source change: ' + str(changed))
        proof = dict(schema=1, candidate=2103306, locked_apk_parent=2103305,
                     locked_skin_parent='1.0.5.196', before=before, after=after,
                     changed=sorted(changed), parent_proof_sha256=digest(args.parent_proof.read_bytes()),
                     locked_parent_receipt_sha256=PARENT_PROOF_SHA256,
                     parent_source_map_sha256=PARENT_SOURCE_MAP_SHA256,
                     provider_python_changed=False, active_skin_adaptation_preserved=True,
                     back_dispatch_policy_changed=False, back_freeze_resolved=False,
                     shutdown_changed=False, weather_changed=False, video_framing_changed=False,
                     physical_device_verified=False, crash_owner_proven=False)
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(proof, indent=2, sort_keys=True) + '\n')
    else:
        proof = json.loads(args.receipt.read_text())
        if proof['candidate'] != 2103306 or set(proof['changed']) != set(FILES):
            raise ValueError('Wrong candidate receipt')
        after = snapshot(args.source)
        mismatches = [n for n, h in proof['after'].items() if after.get(n) != h]
        if mismatches:
            raise ValueError('Source preservation failure: ' + str(mismatches[:20]))
    print('PASS 2103306 provider coordinates', args.command)


if __name__ == '__main__':
    main()
