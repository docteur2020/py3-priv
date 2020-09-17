--- py3/Cparse.py	(original)
+++ py3/Cparse.py	(refactored)
@@ -116,5 +116,5 @@
 		# parse the file
 		parse(fileout)
 
-else: print >> sys.stderr, 'Args: [<.C file in>  <outputfile> ]'
+else: print('Args: [<.C file in>  <outputfile> ]', file=sys.stderr)
 
