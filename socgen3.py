--- py3/socgen.py	(original)
+++ py3/socgen.py	(refactored)
@@ -16,7 +16,7 @@
 	pass
 
 class netmapFile(object):
-    u"""
+    """
      netmapFile: Permet de chercher dans un fichier de type netmap une correspondance.
      format du fichier :
      subnet_id;base_network_address;network_bits;provider;customer;responsible;building_floor;comments;subnet_name
@@ -31,7 +31,7 @@
         try:
             f = open(source)
         except:
-            print >> sys.stderr, "/!\\ PB pour ouvrir le fichier netmap '%s' /!\\" % source
+            print("/!\\ PB pour ouvrir le fichier netmap '%s' /!\\" % source, file=sys.stderr)
             sys.exit(1)
 
         self.__f = f
@@ -46,7 +46,7 @@
         s = csv.reader(self.__f, delimiter=';', quotechar='"')
         for aLine in s:
             if len(aLine) < 9:
-                print >> sys.stderr, "Skip Line : '%s'... Pas assez de champs..." % aLine
+                print("Skip Line : '%s'... Pas assez de champs..." % aLine, file=sys.stderr)
                 continue
             netid = aLine[0]
             base = aLine[1]
@@ -60,7 +60,7 @@
             try:
                 netObj = ipaddr.IPv4Network('%s/%s' % (base, bits))
             except:
-                print >> sys.stderr, "Probleme dans le fichier netmap avec l'entree: '%s/%s'. Je continue..." % (base, bits)
+                print("Probleme dans le fichier netmap avec l'entree: '%s/%s'. Je continue..." % (base, bits), file=sys.stderr)
                 continue
             else:
                 if netObj in hashOfNet:
@@ -73,7 +73,7 @@
                         hashOfNet[netObj] = [
                          netid, network, True, duplicateString, value]
                     except:
-                        print aLine
+                        print(aLine)
                         raise
                     else:
                         continue
