OWAWrapper
==========

This code is designed to permit the invocation of Oracle Pl/Sql procedures
which use the HTP and HTF packages to output HTML to a webpage (that is, the
Oracle Web Access [OWA] toolkit) without requiring the OWA server.
    
This is the same service provided by mod_plsql in later Oracle HTTP servers.
    
This code was written for Plone, but should be useful elsewhere with the 
right tweaks. Be aware, though, that it has exactly as much security as 
Oracle's OWA: which is __very__ little. As written, it is depending on the
security provided by Plone.
    