# -*- coding: utf-8 -*- 

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
#########################################################################

if request.env.web2py_runtime_gae:            # if running on Google App Engine
    db = DAL('gae')                           # connect to Google BigTable
    session.connect(request, response, db=db) # and store sessions and tickets there
    ### or use the following lines to store sessions in Memcache
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db=MEMDB(Client())
else:                                         # else use a normal relational database
    db = DAL('sqlite://coaps.sqlite')       # if not, use SQLite or other DB
## if no need for session
# session.forget()

#########################################################################
## Here is sample code if you need for 
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - crud actions
## comment/uncomment as needed

from gluon.tools import *
auth = Auth(globals(), db)                      # authentication/authorization
auth.settings.hmac_key = 'sha512:b7f0e0d9-5364-4555-9d6a-e2b2cab033bb'
auth.define_tables()                         # creates all needed tables
crud = Crud(globals(), db)                      # for CRUD helpers using auth
service = Service(globals())                   # for json, xml, jsonrpc, xmlrpc, amfrpc

# crud.settings.auth=auth                      # enforces authorization on crud
# mail=Mail()                                  # mailer
# mail.settings.server='smtp.gmail.com:587'    # your SMTP server
# mail.settings.sender='you@gmail.com'         # your email
# mail.settings.login='username:password'      # your credentials or None
# auth.settings.mailer=mail                    # for user email verification
# auth.settings.registration_requires_verification = True
# auth.settings.registration_requires_approval = True
# auth.messages.verify_email = \
#  'Click on the link http://.../user/verify_email/%(key)s to verify your email'
# auth.settings.reset_password_requires_verification = True
# auth.messages.reset_password = \
#  'Click on the link http://.../user/reset_password/%(key)s to reset your password'
## more options discussed in gluon/tools.py
#########################################################################

#########################################################################
## Define your tables below, for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################


common_kwargs = dict(migrate=False)
db.define_table("stations_list",
                *[Field(_) for _ in
                  ('COOPID', 'STATION_NAME',
                   'LONGITUDE', 'LATITUDE', 'ELEVATION',
                   'CROPID', 'COUNTY_WITHIN', 'COUNTY_REPRESENT')],
                 **common_kwargs)

# Averages tables
common_fields = [Field(f, 'string', length=n)
                 for (f, n) in zip(('COOPID', 'ENSOI', 'phase'), (6, 4, 1))]
periods = dict(monthly=['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                        'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC', ],
               JFM=['JFM', 'AMJ', 'JAS', 'OND'],
               DJF=['DJF', 'MAM', 'JJA', 'SON'],
               NDJ=['NDJ', 'FMA', 'MJJ', 'ASO'])

for obsv in ('rain', 'tmin', 'tmax'):
    # Averages tables .................
    for (p, f) in periods.items():
        tbname = "averages_%s_%s" % (p, obsv)
        fields = common_fields
        fields.extend([Field(_, 'double') for _ in f])
        db.define_table(tbname, *fields, **common_kwargs)
# Series tables ...................
table = db.averages_monthly_rain
records = db(table.id > 0).select(table.COOPID).as_list()
coopids = list(set(_['COOPID'] for _ in records))
for obsv in ('rain', 'tmin', 'tmax'):
    fields = [Field("dates", "date")] + \
             [Field("COOP%s" % _, 'double') for _ in coopids]
    tbname = "series_monthly_%s" % obsv
    db.define_table(tbname, *fields, **common_kwargs)
