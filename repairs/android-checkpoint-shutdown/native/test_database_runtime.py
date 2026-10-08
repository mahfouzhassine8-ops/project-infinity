#!/usr/bin/env python3
"""Compile actual integrated DB methods and registry against the real SQLite library."""
import argparse
import ctypes.util
from pathlib import Path
import subprocess
import tempfile

from test_checked_sqlite import extract_function

HERE = Path(__file__).resolve().parent
FUNCTIONS = {
    "dataset.cpp": [
        "void Dataset::post()",
        "void Dataset::del()",
        "void Dataset::deletion()",
    ],
    "sqlitedataset.cpp": [
        "int SqliteDatabase::InfinityAuthorize(",
        "void SqliteDatabase::InfinityRefreshTransaction()",
        "int SqliteDatabase::InfinityExecute(",
        "void SqliteDatabase::start_transaction()",
        "void SqliteDatabase::commit_transaction()",
        "void SqliteDatabase::rollback_transaction()",
        "void SqliteDataset::make_query(",
        "int SqliteDataset::exec(const std::string& sql)",
        "bool SqliteDataset::query(const std::string& query)",
    ],
    "Database.cpp": [
        "void CDatabase::InfinityUpdateQueued()",
        "bool CDatabase::BeginMultipleExecute()",
        "bool CDatabase::CommitMultipleExecute()",
        "bool CDatabase::ExecuteQuery(const std::string& strQuery)",
        "bool CDatabase::QueueInsertQuery(const std::string& strQuery)",
        "bool CDatabase::CommitInsertQueries()",
        "bool CDatabase::QueueDeleteQuery(const std::string& strQuery)",
        "bool CDatabase::CommitDeleteQueries()",
        "void CDatabase::BeginTransaction()",
        "bool CDatabase::CommitTransaction()",
        "void CDatabase::RollbackTransaction()",
    ],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_root.resolve() / "xbmc/dbwrappers"
    methods = []
    for file, signatures in FUNCTIONS.items():
        text = (source / file).read_text()
        methods.extend(extract_function(text, signature) for signature in signatures)
    template = (HERE / "database_runtime_test.cpp.in").read_text()
    assert template.count("// @PRODUCTION_FUNCTIONS@") == 1
    code = template.replace("// @PRODUCTION_FUNCTIONS@", "\n\n".join(methods))
    library = ctypes.util.find_library("sqlite3")
    if not library:
        raise RuntimeError("Real SQLite required")
    linker = library if Path(library).is_absolute() else "-l:" + library
    with tempfile.TemporaryDirectory(prefix="infinity-db-runtime-") as temp:
        root = Path(temp)
        cpp, binary = root / "runtime.cpp", root / "runtime"
        cpp.write_text(code)
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pthread",
                        "-I" + str(source), str(cpp), linker, "-o", str(binary)], check=True)
        subprocess.run([str(binary), str(root)], check=True, timeout=20)

        # Separate process: the unsupported-backend refusal is intentionally
        # irreversible for an engine lifetime. Compile the production registry,
        # Connect admission prefix, full Close and destructor, with only the
        # backing connection teardown replaced by a narrow context shim.
        database_source = (source / "Database.cpp").read_text()
        connect = extract_function(database_source, "bool CDatabase::Connect(")
        prefix = connect[connect.index("{") + 1:connect.index("// create the appropriate database structure")]
        assert 'dbSettings.type != "sqlite3"' in prefix
        assert "InfinityDatabaseBarrier::SetUnsupported(this, true);" in prefix
        closed_owner_code = r'''
#include "InfinityDatabaseBarrier.h"
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
#include <iostream>
namespace InfinityShutdownTrace { struct Scope { Scope(const char*,int,const void*,const void*){} }; }
struct DatabaseSettings { std::string type; };
struct Backing { void disconnect() {} };
struct Dataset { void close() {} };
class CDatabase {
public:
  std::unique_ptr<Backing> m_pDB{new Backing};
  std::unique_ptr<Dataset> m_pDS{new Dataset},m_pDS2{new Dataset};
  unsigned m_openCount=1;
  bool m_multipleExecute=false,m_bMultiInsert=false,m_bMultiDelete=false;
  std::vector<std::string> m_multipleQueries;
  bool ConnectAdmission(const DatabaseSettings& dbSettings);
  void Close(); void InfinityUpdateQueued(); ~CDatabase();
};
// @LIFECYCLE@
void require(bool condition,const char* text){if(!condition)throw std::runtime_error(text);}
int main(){
  {
    CDatabase remote;
    require(remote.ConnectAdmission({"mysql"}),"ordinary remote connection blocked");
    require(InfinityDatabaseBarrier::GetSnapshot().unsupportedOwners>0,"live remote owner absent");
    remote.Close();
    require(InfinityDatabaseBarrier::GetSnapshot().unsupportedOwners>0,"Close hid unsupported remote owner");
  }
  require(InfinityDatabaseBarrier::GetSnapshot().unsupportedOwners>0,"destruction hid unsupported remote owner");
  { CDatabase local; require(local.ConnectAdmission({"sqlite3"}),"ordinary sqlite connection blocked"); }
  { int owner=0; InfinityDatabaseBarrier::Operation operation(&owner);
    require(operation.AllowWrite(),"unsupported history disabled ordinary runtime"); }
  require(InfinityDatabaseBarrier::Begin(1),"begin failed");
  require(!InfinityDatabaseBarrier::GetSnapshot().Ready(),"closed remote owner allowed checkpoint");
  require(!InfinityDatabaseBarrier::Seal(1),"closed remote owner sealed");
  require(InfinityDatabaseBarrier::End(1),"explicit recovery failed");
  require(InfinityDatabaseBarrier::Begin(2),"second begin failed");
  require(!InfinityDatabaseBarrier::GetSnapshot().Ready(),"new session forgot remote history");
  require(!InfinityDatabaseBarrier::Seal(2),"second session sealed remote history");
  std::cout<<"PASS closed_unsupported_backend_remains_process_lifetime_refusal\n";
}
'''
        lifecycle = [
            "bool CDatabase::ConnectAdmission(const DatabaseSettings& dbSettings) {" + prefix + "return true;}",
            extract_function(database_source, "void CDatabase::Close()"),
            extract_function(database_source, "void CDatabase::InfinityUpdateQueued()"),
            extract_function(database_source, "CDatabase::~CDatabase(void)"),
        ]
        cpp.write_text(closed_owner_code.replace("// @LIFECYCLE@", "\n".join(lifecycle)))
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pthread",
                        "-I" + str(source), str(cpp), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=10)


if __name__ == "__main__":
    main()
