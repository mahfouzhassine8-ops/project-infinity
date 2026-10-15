#!/usr/bin/env python3
"""Apply the reviewed 2103327 transform with the exact CJobManager declaration anchor."""
import native_repair


def transform_header(text: str) -> str:
    old = '''  /*!
   \\brief Cancel all remaining jobs, preparing for shutdown
   Should be called prior to destroying any objects that may be being used as callbacks
   \\sa CancelJob(), AddJob()
   */
  void CancelJobs();
'''
    new = '''  /*!
   \\brief Begin cooperative job shutdown without waiting for active workers
   Rejects new jobs, releases queued work and marks active work cancelled.
   Final worker completion remains owned by CancelJobs().
   */
  void BeginShutdown();

  /*!
   \\brief Cancel all remaining jobs, preparing for shutdown
   Should be called prior to destroying any objects that may be being used as callbacks
   \\sa CancelJob(), AddJob()
   */
  void CancelJobs();
'''
    text = native_repair.once(text, old, new)
    return native_repair.once(
        text,
        '  CJob *PopJob();\n',
        '  unsigned int GetJobId(const CJob* job) const;\n\n  CJob *PopJob();\n')


native_repair.transform_header = transform_header
native_repair.main()
