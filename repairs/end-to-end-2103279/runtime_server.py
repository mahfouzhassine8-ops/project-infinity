from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
import json,os,time
os.chdir('runtime-media')
class Handler(SimpleHTTPRequestHandler):
 def do_GET(self):
  u=urlparse(self.path);q=parse_qs(u.query);action=q.get('action',[''])[0]
  if u.path=='/player_api.php':
   base='http://10.0.2.2:8765';category=[{'category_id':'1','category_name':'Audit collection'}]
   info={'name':'Audit movie','plot':'Generated local audit content','genre':'Test','duration_secs':180,'year':'2026','youtube_trailer':base+'/wide.mp4','movie_image':base+'/poster.jpg'}
   payload={'user_info':{'auth':1,'status':'Active','max_connections':'8','active_cons':'0'},'server_info':{'timezone':'UTC'}}
   if action in ['get_live_streams','get_live_categories']:payload=[]
   elif action in ['get_vod_categories','get_series_categories']:payload=category
   elif action=='get_vod_streams':payload=[{'stream_id':'101','name':'Audit movie','category_id':'1','stream_icon':base+'/poster.jpg','container_extension':'mp4','added':str(int(time.time())),'rating':'8','year':'2026'}]
   elif action=='get_series':payload=[{'series_id':'201','name':'Audit show','category_id':'1','cover':base+'/poster.jpg','last_modified':str(int(time.time())),'rating':'8','year':'2026'}]
   elif action=='get_vod_info':payload={'info':info,'movie_data':{'stream_id':'101','name':'Audit movie','container_extension':'mp4'}}
   elif action=='get_series_info':payload={'info':dict(info,name='Audit show'),'episodes':{'1':[{'id':'301','title':'Audit episode','season':1,'episode_num':1,'container_extension':'mp4','info':{'plot':'Generated episode','duration_secs':180}}]},'seasons':[{'season_number':1,'episode_count':1}]}
   data=json.dumps(payload).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
  if u.path.startswith('/movie/') or u.path.startswith('/series/'):self.path='/wide.mp4'
  super().do_GET()
ThreadingHTTPServer(('0.0.0.0',8765),Handler).serve_forever()
