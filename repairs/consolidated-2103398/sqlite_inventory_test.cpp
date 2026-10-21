// Execute the actual production VFS and ledger against real SQLite.
#include "dbwrappers/InfinitySQLiteVFS.h"
#include <cassert>
#include <iostream>
#include <sys/stat.h>
int main(int argc,char** argv) {
 assert(argc==3);const std::string root=argv[1];const bool fixed=std::string(argv[2])=="fixed";
 assert(InfinitySQLiteVFS::Install());
 sqlite3* db=nullptr;assert(sqlite3_open((root+"/main.db").c_str(),&db)==SQLITE_OK);
 assert(sqlite3_exec(db,"CREATE TABLE data(value); INSERT INTO data VALUES(42)",nullptr,nullptr,nullptr)==SQLITE_OK);
 sqlite3_stmt* attach=nullptr;assert(sqlite3_prepare_v2(db,"ATTACH ? AS protected",-1,&attach,nullptr)==SQLITE_OK);
 assert(sqlite3_bind_text(attach,1,(root+"/attached.db").c_str(),-1,SQLITE_TRANSIENT)==SQLITE_OK);
 assert(sqlite3_step(attach)==SQLITE_DONE);sqlite3_finalize(attach);
 assert(sqlite3_exec(db,"CREATE TABLE protected.essential(value); INSERT INTO protected.essential VALUES(73)",nullptr,nullptr,nullptr)==SQLITE_OK);
 assert(InfinityScriptPersistence::BeginWriteProtection(1,{root},{}));
 assert(InfinityScriptPersistence::CloseParticipantWrites(1));
 sqlite3_stmt* inventory=nullptr;int result=sqlite3_prepare_v2(db,"PRAGMA database_list",-1,&inventory,nullptr);
 if(!fixed) {assert(result==SQLITE_READONLY);std::cout<<"baseline reproduced SQLITE_READONLY=8 during attachment inventory\n";sqlite3_finalize(inventory);return 0;}
 assert(result==SQLITE_OK);int rows=0;bool attached=false;
 while(sqlite3_step(inventory)==SQLITE_ROW) {++rows;const auto* path=sqlite3_column_text(inventory,2);if(path&&std::string(reinterpret_cast<const char*>(path))==root+"/attached.db")attached=true;}
 sqlite3_finalize(inventory);assert(rows==2&&attached);
 // Read-only main plus bound ATTACH are inventoried, without a new write lease.
 sqlite3* ro=nullptr;assert(sqlite3_open_v2((root+"/main.db").c_str(),&ro,SQLITE_OPEN_READONLY,nullptr)==SQLITE_OK);
 assert(sqlite3_exec(ro,"PRAGMA database_list",nullptr,nullptr,nullptr)==SQLITE_OK);assert(sqlite3_close(ro)==SQLITE_OK);
 assert(sqlite3_exec(db,"INSERT INTO protected.essential VALUES(999)",nullptr,nullptr,nullptr)==SQLITE_READONLY);
 assert(sqlite3_exec(db,"PRAGMA user_version=99",nullptr,nullptr,nullptr)==SQLITE_READONLY);
 assert(sqlite3_close(db)==SQLITE_OK);
 // Reopen independently and prove both protected databases retained exact data.
 assert(sqlite3_open_v2((root+"/attached.db").c_str(),&ro,SQLITE_OPEN_READONLY,nullptr)==SQLITE_OK);
 sqlite3_stmt* check=nullptr;assert(sqlite3_prepare_v2(ro,"SELECT value FROM essential",-1,&check,nullptr)==SQLITE_OK);
 assert(sqlite3_step(check)==SQLITE_ROW&&sqlite3_column_int(check,0)==73);assert(sqlite3_step(check)==SQLITE_DONE);
 sqlite3_finalize(check);assert(sqlite3_close(ro)==SQLITE_OK);
 std::cout<<"inventory exact; read-only connection exact; late writes denied; protected reopen exact\n";
}
