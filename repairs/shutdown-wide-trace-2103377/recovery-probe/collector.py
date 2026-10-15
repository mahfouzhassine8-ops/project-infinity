"""Read-only recovery of allowlisted native evidence and installed source identity."""
import hashlib,json,os,re,stat,time,zipfile
import probe
with open(os.path.join(os.path.dirname(__file__),'vocabulary.json'),'r',encoding='utf-8') as vocabulary_file:
    VOCABULARY=frozenset(json.load(vocabulary_file))
OWNER_NAMES=frozenset(('native_admission python_services background_jobs playback command_center compat '
 'kodi_settings profiles skin_settings addon_settings favourites peripherals audio_policy '
 'deferred_dialog_state xml_files native_databases pvr').split())
IDS=('plugin.video.playlistbrowser','plugin.video.redlight','plugin.video.seren',
 'plugin.video.tmdb.bingie.helper','plugin.video.tmdbmovies','plugin.video.youtube',
 'plugin.video.youtubek','repository.zeus768')
NATIVE_FILES=('infinity-shutdown-native.jsonl.critical',
              'infinity-shutdown-native.jsonl.critical.previous')
MAX_NATIVE_BYTES=16*1024*1024
MAX_LINE_BYTES=4096
NUMERIC_FIELDS=frozenset(('schema seq pid tid session_start_ns boot_ns monotonic_ns epoch_ns '
 'invoker_id span_id parent_span_id duration_ns operation_id operation_parent_id checkpoint_generation '
 'operation_start_monotonic_ns stage_start_monotonic_ns operation_end_monotonic_ns operation_worker_tid '
 'backend_identity_observed backend_cancel_callback_observed cancellation_outcome_bits '
 'subject_execution_id subject_start_monotonic_ns subject_worker_tid '
 'checkpoint_outcome_observed_monotonic_ns lane').split())
CATEGORY_FIELDS=frozenset(('kind phase engine backend_category operation_kind operation_stage '
 'resource_category cancellation_support owner_kind').split())
OUTCOMES=frozenset(('observed true false positive negative zero void_return unclassified '
 'scope_returned scope_unwound scope_returned_not_success scope_unwound_not_success '
 'snapshot_at_request checkpoint_request_not_backend_cancel native_request_accepted '
 'CHECKPOINT_FAILED SAFE_TO_TERMINATE native_failure_observed native_safe_observed '
 'callback_entered existing_flag_set callback_returned cancel_flag_seen_by_loop '
 'callback_exception_unwound callback_returned_operation_still_active '
 'callback_returned_operation_no_longer_active callback_observed_no_matching_active_operation '
 'monitor_notification_sent cooperative_stop_called escalation_stop_called legacy_abort_flag_set '
 'async_python_exception_set no_active_operation_observed '
 'durability_receipt_taken no_durability_receipt before_Py_EndInterpreter '
 'Py_EndInterpreter_returned_not_durability_proof existing_event_set_not_native_thread_death '
 'no_other_interpreter_thread_states_observed other_interpreter_thread_state_observed '
 'ExitReported_callback_not_OS_death ExceptionReported_callback_not_OS_death '
 'blocking_StopThread_returned nonblocking_stop_not_join_proof '
 'frame_observed no_python_frame started stop_returned stop_rejected waiting '
 'concrete_type_observed unclassified_concrete_type no_backend_object '
 'factory_choice_not_concrete_identity previous_stage_ending executing '
 'bytecode_returned waiting_child_states child_states_retired interpreter_finalizing '
 'interpreter_end_returned stopped_event_set retirement_ledger_read native_exit_callback '
 'active_at_capture_begin exception_unwound evidence_incomplete truncated '
 'native_scope_snapshot_changed bounded_concurrent_snapshot_unavailable '
 'concurrent_last_return_not_retained subject_capacity_exhausted operation_capacity_exhausted '
 'file_owner_capacity_exhausted native_scope_capacity_exhausted').split())

def filtered_row(row):
    result={}
    for key,value in row.items():
        if key in NUMERIC_FIELDS and type(value) is int:result[key]=value
        elif key in CATEGORY_FIELDS:
            result[key]=value if isinstance(value,str) and value in VOCABULARY else 'withheld_unrecognized_category'
        elif key=='addon_id':
            result[key]=value if value in IDS or value in ('','script.infinity.commandcenter','service.infinity.compat') else 'other_addon'
        elif key=='outcome':
            numeric=isinstance(value,str) and re.fullmatch(
              r'(curl_result_code_-?[0-9]+|completed_calls_[0-9]+_total_ns_[0-9]+|'
              r'gen_[0-9]+_durable_[0-9]+_dirty_[01]_complete_[01]_error_[01]_active_writes_[0-9]+)',value)
            result[key]=value if (isinstance(value,str) and value in OUTCOMES) or numeric else 'withheld_nonfixed_outcome'
        elif key=='target_thread' and isinstance(value,str):
            # Native thread-state targets and source-code frame locations only.
            if value in OWNER_NAMES or re.fullmatch(r'(os_tid\.[0-9]+\.stage\.[A-Za-z_]+|[0-9]+|'
              r'(sqlite|database)\.(close|commit|rollback))',value):result[key]=value
            else:
                parts=value.split(':')
                if len(parts)==4 and parts[0].isdigit() and parts[2].isdigit():
                    source=parts[1] if parts[1] in ('<string>','main.py','service.py','default.py','__init__.py') else 'source_withheld'
                    function=parts[3] if parts[3] in probe.SAFE_SYMBOLS or parts[3] in ('read_text','refresh_playlist','_vfs_file','_vfs_try','__call__') else 'function_withheld'
                    result[key]=':'.join((parts[0],source,parts[2],function))
    return result

def read_native(root,name):
    if name not in NATIVE_FILES:raise probe.ProbeError('trace_name_not_allowed')
    root=probe._safe_local_root(root);directory=probe._open_local_directory(root);fd=None
    try:
        fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory)
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1:raise probe.ProbeError('nonregular_trace_refused')
        if before.st_size>MAX_NATIVE_BYTES:raise probe.ProbeError('trace_size_bound')
        digest=hashlib.sha256();data=bytearray();rows=[];invalid=0
        while True:
            block=os.read(fd,65536)
            if not block:break
            digest.update(block);data.extend(block)
            if len(data)>MAX_NATIVE_BYTES:raise probe.ProbeError('trace_size_bound')
        after=os.fstat(fd)
        changed=(before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns)
        for line in data.splitlines():
            if len(line)>MAX_LINE_BYTES:invalid+=1;continue
            try:
                item=json.loads(line)
                if not isinstance(item,dict):raise ValueError()
                rows.append(filtered_row(item))
            except (ValueError,UnicodeError):invalid+=1
        encoded=''.join(json.dumps(r,separators=(',',':'),sort_keys=True)+'\n' for r in rows).encode()
        return encoded,{'source_bytes':len(data),'source_sha256':digest.hexdigest(),
          'filtered_rows':len(rows),'invalid_or_oversized_lines':invalid,'changed_during_read':changed,
          'source_snapshot_atomic':not changed,'raw_strings_or_unknown_fields_exported':False}
    finally:
        if fd is not None:os.close(fd)
        os.close(directory)

def export(destination,installed_roots,trace_root):
    destination=probe._safe_local_root(destination);reports=[];traces={}
    for addon_id in IDS:
        root=installed_roots.get(addon_id)
        if not root:reports.append({'addon_id':addon_id,'status':'installed_root_unavailable'});continue
        probe.ADDON_ID=addon_id
        try:reports.append({'addon_id':addon_id,'evidence':probe.collect(root)})
        except Exception:reports.append({'addon_id':addon_id,'status':'installed_code_unavailable'})
    manifest={'schema':1,'collector':'Infinity shutdown evidence recovery 0.1.0',
      'source_identity':reports,'native_files':{},'classification':'UNKNOWN until dependencies and write behavior verified',
      'shutdown_repaired':False,'new_shutdown_test_required':False,'private_userdata_collected':False}
    for name in NATIVE_FILES:
        try:
            data,info=read_native(trace_root,name);traces['native/'+name]=data;manifest['native_files'][name]=info
        except Exception:manifest['native_files'][name]={'status':'allowlisted_trace_unavailable'}
    # New diagnostic output only; never overwrite the protected app or a prior export.
    name='Infinity-Shutdown-Recovery-%s-%s.zip'%(time.strftime('%Y%m%d-%H%M%S'),os.urandom(4).hex())
    directory=probe._open_local_directory(destination);fd=None;created=False
    try:
        fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=directory);created=True
        with os.fdopen(fd,'wb') as stream:
            fd=None
            with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
                z.writestr('recovery.json',json.dumps(manifest,indent=2,sort_keys=True))
                for entry,data in traces.items():z.writestr(entry,data)
            stream.flush();os.fsync(stream.fileno())
        os.fsync(directory);return os.path.join(destination,name)
    except Exception:
        if created:
            try:os.unlink(name,dir_fd=directory)
            except OSError:pass
        raise
    finally:
        if fd is not None:os.close(fd)
        os.close(directory)
