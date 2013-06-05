import sys
import argparse
from WikiFormatter import WikiFormatter

parser = argparse.ArgumentParser(description='Import content from Trac into MediaWiki')
parser.add_argument('--mwiki-host', type=str, help="MediaWiki URL", default="localhost")
parser.add_argument('--mwiki-path', type=str, help="MediaWiki Path [/mediawiki/]", default="")
parser.add_argument('--mwiki-user', type=str, help="MediaWiki Username", default="")
parser.add_argument('--mwiki-pass', type=str, help="MediaWiki Password", default="")
parser.add_argument('--mwiki-port', type=int, help="MediaWiki Port, default 80", default=80)	
parser.add_argument('--trac-path', type=str, help="Trac installation directory", default="/home/trac/trac")
parser.add_argument('--sqlite-db', type=str, help="Trac source database", default=None)
parser.add_argument('--prefix', type=str, help="Prefix for pages imported into MediaWiki", default="")

args = parser.parse_args()

import mwclient


#Init mwclient
mwsite = mwclient.Site("%s:%s" % (args.mwiki_host, args.mwiki_port),  path=args.mwiki_path)
mwsite.login(args.mwiki_user, args.mwiki_pass)

if 'edit' not in mwsite.rights:
	raise Exception("%(mwiki_user)s does not have edit permissions on %(mwiki_host)s" % args)
if 'createpage' not in mwsite.rights:
	raise Exception("%(mwiki_user)s does not have page creation permissions on %(mwiki_host)s" % args)
	
if args.sqlite_db is not None:
	import sqlite3
	sqliteconn = sqlite3.connect(args.sqlite_db)
	traccur = sqliteconn.cursor()
elif args.trac_path is not None:
	from trac.env import Environment	
	tracenv = Environment(args.trac_path)
	tracdb = tracenv.get_db_cnx()
	traccur = tracdb.cursor()

if args.prefix != "":
	args.prefix = "%s - " % args.prefix

traccur.execute("SELECT `name`, `author`, `text`, `comment` FROM `wiki` ORDER BY `version` ASC")
for page in traccur:
	#Format the page from Trac to MW format
	formatter = WikiFormatter(page[2])

	newpage = {}
	newpage['name'] = "%s%s" % (args.prefix, page[0])
	newpage['author'] = page[1]
	newpage['text'] = formatter.parse()
	newpage['comment'] = page[3]
	
	#lets actually create the page now

	mwsite.Pages[newpage['name']].save(newpage['text'], summary=newpage['comment'])
	
