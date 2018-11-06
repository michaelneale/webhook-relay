# heavily borrowing from: https://github.com/hiroakis/tornado-websocket-example

from tornado import websocket, web, ioloop
from tornado.ioloop import PeriodicCallback
import json

# here we keep the currently connected clients
clients = {}

# Here we can keep things to store and forward if a cient reconnects
store = {}

class IndexHandler(web.RequestHandler):
    def get(self):
        self.render("index.html")

class SocketHandler(websocket.WebSocketHandler):
    
    def check_origin(self, origin):
        return True

    def open(self):  
        self.timeout = None            
        self.callback = PeriodicCallback(self.send_hello, 20000)
        self.callback.start()
        tenant = self.request.uri.split('/subscribe/')[1]
        clients[tenant] = self
        self.flush_messages(tenant)
    
    # keep the connection alive through proxies as much as possible    
    def send_hello(self):
        self.ping('ping')
        
    # see if there are any messages to forward on          
    def flush_messages(self, tenant):
        if tenant in store: 
            messages = store[tenant]
            for payload in messages:                
                self.write_message(json.dumps(payload, ensure_ascii=False))                    
        store[tenant] = []

    def on_close(self):
        self.callback.stop()
        tenant = self.request.uri.split('/subscribe/')[1]
        if tenant in clients: 
            del clients[tenant]
                    

class ApiHandler(web.RequestHandler):

    @web.asynchronous
    def get(self, *args):
        self.finish()

    @web.asynchronous
    def post(self, *args):
        publishedUri = self.request.uri.split('/publish/')[1]
        tenant = publishedUri.split('/')[0]
        endpoint = "/" + "/".join(publishedUri.split('/')[1:])
        headers = {}
        for header in self.request.headers:
            headers[header] = self.request.headers[header]        
        payload = {'headers': headers, 'requestPath': endpoint, 'body': self.request.body}
        
        if tenant in clients:
            clients[tenant].write_message(json.dumps(payload, ensure_ascii=False))
        else:
            self.store_message(tenant, payload)
                
        self.finish()

    # Keep for later        
    def store_message(self, tenant, payload):
        if tenant in store:
            store[tenant].append(payload)

app = web.Application([
    (r'/', IndexHandler),
    (r'/subscribe/.*', SocketHandler),
    (r'/publish/.*', ApiHandler),
    (r'/(favicon.ico)', web.StaticFileHandler, {'path': '../'}),
    (r'/(rest_api_example.png)', web.StaticFileHandler, {'path': './'}),
])

if __name__ == '__main__':
    app.listen(8080)
    ioloop.IOLoop.instance().start()
