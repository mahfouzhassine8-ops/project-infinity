#!/usr/bin/env python3
"""Create a two-file overlay from the exact 2103334/2103335 native preimage.

This prerequisite does not activate Android checkpoint shutdown or emit SAFE.
The preservation parent is never modified; output must be a separate empty path.
"""

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SQLITE = "xbmc/dbwrappers/sqlitedataset.cpp"
DATABASE = "xbmc/dbwrappers/Database.cpp"
PREIMAGES = json.loads((HERE / "preimages.json").read_text())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError("Expected exactly one original function: " + before.splitlines()[0])
    return text.replace(before, after, 1)


def transaction_functions(operation):
    method, sql, old_state = {
        "begin": ("start_transaction", "begin IMMEDIATE", "true"),
        "commit": ("commit_transaction", "commit", "false"),
        "rollback": ("rollback_transaction", "rollback", "false"),
    }[operation]
    trace = (
        f'  InfinityShutdownTrace::Scope methodEvidence("sqlite.{operation}", -1, nullptr, nullptr);\n'
        if operation != "begin" else ""
    )
    before = f'''void SqliteDatabase::{method}()
{{
{trace}  if (active)
  {{
    sqlite3_exec(conn, "{sql}", NULL, NULL, NULL);
    _in_transaction = {old_state};
  }}
}}'''
    after = f'''void SqliteDatabase::{method}()
{{
{trace}  // INFINITY_CHECKED_SQLITE: never acknowledge a transaction that SQLite rejected.
  if (!active || conn == nullptr)
  {{
    _in_transaction = false;
    throw DbErrors("SQLite {operation} requires an active connection");
  }}

  const int result = sqlite3_exec(conn, "{sql}", NULL, NULL, NULL);
  // BUSY/constraint/authorization failures can leave the transaction active;
  // some I/O errors roll it back. SQLite is authoritative in either case.
  _in_transaction = sqlite3_get_autocommit(conn) == 0;
  if (result != SQLITE_OK)
  {{
    setErr(result, "{sql}");
    throw DbErrors("%s", getErrorMsg());
  }}
}}'''
    return before, after


def transform(name, data):
    if name not in PREIMAGES or digest(data) != PREIMAGES[name]:
        raise ValueError("2103334 preimage hash mismatch: " + name)
    text = data.decode("utf-8")
    if name == SQLITE:
        for operation in ("begin", "commit", "rollback"):
            text = replace_once(text, *transaction_functions(operation))
    elif name == DATABASE:
        before = '''bool CDatabase::CommitTransaction()
{
  InfinityShutdownTrace::Scope methodEvidence("database.commit", -1, nullptr, nullptr);
  try
  {
    if (nullptr != m_pDB)
      m_pDB->commit_transaction();
  }
  catch (...)
  {
    CLog::Log(LOGERROR, "database:committransaction failed");
    return false;
  }
  return true;
}'''
        after = '''bool CDatabase::CommitTransaction()
{
  InfinityShutdownTrace::Scope methodEvidence("database.commit", -1, nullptr, nullptr);
  try
  {
    // INFINITY_CHECKED_SQLITE: an absent connection is not a successful commit.
    if (nullptr == m_pDB)
    {
      CLog::Log(LOGERROR, "database:committransaction failed (database not open)");
      return false;
    }
    m_pDB->commit_transaction();
  }
  catch (...)
  {
    CLog::Log(LOGERROR, "database:committransaction failed");
    return false;
  }
  return true;
}'''
        text = replace_once(text, before, after)
    return text.encode("utf-8")


def prepare(source_root):
    # Validate every file before returning anything that can be written.
    originals = {name: (source_root / name).read_bytes() for name in PREIMAGES}
    changed = {name: transform(name, data) for name, data in originals.items()}
    return changed


def create_overlay(source_root, output_root):
    source_root = source_root.resolve()
    output_root = output_root.resolve()
    if (source_root == output_root or source_root in output_root.parents or
            output_root in source_root.parents):
        raise ValueError("Overlay must be separate from the preservation source tree")
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError("Overlay destination must be empty")
    changed = prepare(source_root)
    for name, data in changed.items():
        path = output_root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    receipt = {
        "kind": "checked-sqlite-prerequisite-overlay-v1",
        "preservation_parent": "2103334 native engine inherited byte-identically by 2103335",
        "source_root": str(source_root),
        "preimages": PREIMAGES,
        "postimages": {name: digest(data) for name, data in changed.items()},
        "normal_close_route_activated": False,
        "safe_to_terminate_implemented": False,
    }
    (output_root / "checked-sqlite-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(create_overlay(args.source_root, args.output_root), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
