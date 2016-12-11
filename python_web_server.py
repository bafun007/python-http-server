#!/usr/bin/env python
"""
Simple HTTP server in python.  This script will save the log data int Data.txt
Usage::
	./python_web_server.py [<port>] [<logFile>] -- default port is 12345 and logFile is Data.txt
Send a GET request::
	curl http://localhost
Send a HEAD request::
	curl -I http://localhost
Send a POST request::
	curl -d "foo=bar&bin=baz" http://localhost
"""
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import json
import io
import csv


logFile = 'Data.json'
dataTable = 'AnalyzedDataTable.json'
port = 12345
tabObj = {}
savedTabObj = {}

# Make jason tree structure where input keys/value pairs are define as [{xyz.abc.def.jkl, "My Private Data"}, ....]
def do_Tree(data):
	d={}
	for f in data.keys():
		dd=d
		kk=f.split('.')
		n=len(kk)
		for a in kk:
			n -= 1
			if(n>0):
				if a not in dd:
					dd[a]={}
				dd=dd[a]
			else:
				dd[a]=data[f]
				break;
	return d

def save_Data(pdata):
	print (json.dumps(pdata, indent=4))
	f = open(logFile, 'aw+')
	f.write(unicode(json.dumps(pdata, indent=4)))
	f.write('\n')
	f.close()


class S(BaseHTTPRequestHandler):

	def _set_headers(self):
		self.send_response(200)
		self.send_header('Content-type', 'text/html')
		self.end_headers()

	def do_GET(self):
		self._set_headers()
		self.wfile.write("<html><body><h1>hi!</h1></body></html>")

	def do_HEAD(self):
		self._set_headers()

		   
	def do_POST(self):
		self._set_headers()

		print "in post method"
		self.data_string = self.rfile.read(int(self.headers['Content-Length']))

		self.send_response(200)
		self.end_headers()
		listObj = {}
		
		# Check if the data_string is json format
		try:
			pdata = json.loads(self.data_string)
		except ValueError as e:
			# Not json format.  Just record the data 
			save_Data(self.data_string)
			return
			
		# convert the incoming tr181 data from csv to json format 
		if ('data_format' in pdata) and ('csv' == pdata["data_format"]):
			if 'payload' in pdata:
				payload = pdata["payload"].split('\n')
				mylist = list(csv.reader(payload))
				if (len(mylist) > 2):
					[r.pop(1) for r in mylist]
					[r.pop(2) for r in mylist]
				for r in mylist:
					listObj[r[0]] = r[1].strip()
				pdata["payload"] = do_Tree(listObj)
			elif 'data' in pdata:
				for r in pdata['data']:
					dd=r.split(',')
					listObj[dd[0]] = dd[2].strip()
				pdata["data"] = do_Tree(listObj)
				# Create table structure for data analysis
				for r in listObj.keys():
					if r not in savedTabObj:                                
						savedTabObj[r] = listObj[r]
						# tabObj[r][pdata['timestamp']] = listObj[r]
					elif savedTabObj[r] != listObj[r]:  # record only the changed data 
						savedTabObj[r] = listObj[r]
						if r not in tabObj:
							tabObj[r] = {}
						tabObj[r][pdata['timestamp']] = listObj[r]
				# save analysis data table
				with io.open(dataTable, 'w', encoding='utf-8') as f:
					f.write(unicode(json.dumps(tabObj, indent=4)))
		else:
			print "Not csv format"
		# print "{}".format(pdata)
		print (json.dumps(pdata, indent=4))        
		# print (json.dumps(tabObj, indent=4))
	
		# Save full data from TR181 datasource       
		save_Data(pdata)


def run(server_class=HTTPServer, handler_class=S, port=port):
	server_address = ('', port)
	httpd = server_class(server_address, handler_class)
	print 'Starting httpd...'
	httpd.serve_forever()

if __name__ == "__main__":
	from sys import argv

	if len(argv) == 2:
		run(port=int(argv[1]))
	elif len(argv) == 3:
		logFile=argv[2]
		run(port=int(argv[1]))
	else:
		run()

