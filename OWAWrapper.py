# -*- coding: utf-8 -*-
#
# File: OWAWrapper.py
#
# Copyright (c) 2012 by Pointer Stop Consulting, Inc.
# Generator: ArchGenXML Version 2.7
#            http://plone.org/products/archgenxml
#
# GNU General Public License (GPL)
#

__author__ = """Derek Broughton <derek@pointerstop.ca>"""
__docformat__ = 'plaintext'

##code-section module-header #fill in your manual code here
import os
from cx_Oracle import NUMBER, STRING
from Products.Archetypes.atapi import log
from Products.VirtualDataCentre.config import VDCLogLevel
##/code-section module-header

from zope import interface
from zope import component
from Products.CMFPlone import utils
from Products.Five import BrowserView
from zope.interface import implements

from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin


class OWAWrapper(BrowserView):
    """
    """

    ##code-section class-header_OWAWrapper #fill in your manual code here
    ##/code-section class-header_OWAWrapper



    def __call__(self):
        """
        Any invocation of this view with a form parameter ?proc=NAME will invoke the pl/sql procedure 'NAME'
        By default, browser.zcml contains a view definition named "plsql" on the ISiteRoot interface, which means
        that invocation is:
            http://vdc.domain.name/plsql?proc=NAME&arg1=x&arg2=y...
        """
        # get the standard CGI environment variables - they will be passed into the SQL procedure we're building
        environ = self.request.environ
        env_names = [ x for x in [
            'SERVER_SOFTWARE','SERVER_NAME',    'GATEWAY_INTERFACE',
            'REMOTE_HOST',    'REMOTE_ADDR',    'AUTH_TYPE',
            'REMOTE_USER',    'HTTP_ACCEPT',
            'HTTP_USER_AGENT','SERVER_PROTOCOL','SERVER_PORT',
            'SCRIPT_NAME',    'PATH_INFO',      'PATH_TRANSLATED',
            'HTTP_REFERER',   'HTTP_COOKIE']
            if environ.has_key(x)]
        #
        defines = "\n".join(["    env_names(%i):='%s';env_values(%i):='%s';" % (ix+1, key, ix+1, environ[key])
                             for ix,key in enumerate(env_names)])
        param = self.request.form
        # get the pl/sql procedure name
        procedure = param.pop('proc')
        # any other form parameters are to be passed as arguments to the procedure 'proc'
        argList = ",".join(["%s=>'%s'" % (x,param[x]) for x in param])
        log(locals(), level=VDCLogLevel)
        # Now build an inline pl/sql procedure
        # - define arrays to store the environment variables
        # - assign the values using '%(define)s'
        # - call owa.init_cgi_env so that the environment variables will be available to any other procedure
        # - print a single space just to trigger the OWA_CACHE and OWA_UTIL functions:
        #    a little whitespace never hurts HTTP output
        # - finally invoke the procedure with the constructed argument list
        sql  = """
            Declare
              env_names owa.vc_arr;
              env_values owa.vc_arr;
            BEGIN
            %(defines)s
                owa.init_cgi_env(env_names.count, env_names, env_values);
                begin                        --    first invocation of htp.prn calls OWA_CACHE and OWA_UTIL
                    htp.prn(' ');            --    since this breaks when run as a batch job, one htp.prn() will
                exception when others then   --    turn off the "first time" flag, and the handler catches the
                    NULL;                    --    exception
                end;

              %(procedure)s(%(argList)s);
            END;
        """ % locals()
        log(sql, level=VDCLogLevel)

        # find the oracle connection
        cursor = self.context.vdc_db._wrapper.connection.cursor()
        # and execute the inline procedure constructed above
        cursor.execute(sql)

        # create oracle variables to hold:
        # - the number of lines of output to be requested at once,
        numLinesVar = cursor.var(NUMBER)
        # - the output buffer
        linesVar = cursor.arrayvar(STRING, 1000)
        numLinesVar.setvalue(0, 1000)
        output = False
        result = ""
        numLines = 1000
        # Call htp.get_page, getting up to 1000 lines at a time - if we get the full 1000, repeat until we get fewer
        while numLines == 1000:
            cursor.callproc("htp.get_page", (linesVar, numLinesVar))
            numLines = int(numLinesVar.getvalue())
            lines =  ''.join(linesVar.getvalue()[:numLines])
            # throw away lines until we get to the first '<'
            if output:
                result += lines
            else:
                split  = lines.split('<',1)
                if len(split) > 1:
                    result = '<' + split[1]
                    output = True
        # Aug 16, 2012 - ADJ Bug 184 fix
        result=result.replace('HREF="mflib', 'HREF="http://'+ environ.get('HTTP_X_FORWARDED_HOST')+'/plsql?proc=mflib')
        # Aug 29, 2012 - ADJ Bug 211 fix
        result=result.replace('ACTION="/plonescript/','ACTION="http://'+environ.get('HTTP_X_FORWARDED_HOST')+'/plonescript/')
        # Sept 6, 2012 - images are not referenced correctly
        result=result.replace('SRC="/','SRC="http://'+environ.get('HTTP_X_FORWARDED_HOST')+'/')
        return result


##code-section module-footer #fill in your manual code here
##/code-section module-footer
