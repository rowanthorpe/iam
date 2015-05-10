#!/usr/bin/picolisp /usr/lib/picolisp/lib.l

# © Copyright 2014, 2015 Rowan Thorpe
#
# This file is part of iam
#
# iam is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iam is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with iam.  If not, see <http://www.gnu.org/licenses/>.

# v0.1 - plaintext files, basic lisp/xml/html, no auth, not using proper assoc-lists,
#        no file caching, etc

(load "@lib/misc.l")
(load "@lib/http.l")
(load "@lib/xml.l")
(load "@lib/xhtml.l")

(let (arglist (argv))
  (if arglist (setq *Command (pop 'arglist)))    # "server" or "rotate-logs"
  (if arglist (setq *ConfigFile (pop 'arglist))) # custom config-file path
  (if arglist (setq *Names arglist)) )           # remaining args are a list of usernames to allow (override list from config)

(ifn *ConfigFile
     (setq *ConfigFile "/etc/iam_config.l") )
(setq *ConfigStr
      (glue "^j"
            (mapcar pack
                    (in *ConfigFile
                        (make
                         (while (not (eof))
                           (let (myline (line) choppedline (chop myline))
                             (while (and (not (== NIL choppedline)) (sp? (car choppedline)))
                               (pop 'choppedline) )
                             (if (not (= ";" (car choppedline)))
                                 (link myline) ) ) ) ) ) ) ) )
(setq *Config (any *ConfigStr))

(setq *LogDir
      (pack (list
             (last (assoc 'logdir
                          (cdr (assoc 'daemon *Config)) ))
             "/statuses" ) ) )
(setq *Port
      (last (assoc 'port
                  (cdr (assoc 'common *Config)) )) )
(ifn *Names
     (setq *Names
           (cdr (assoc 'users
                       (cdr (assoc 'daemon *Config)) )) ) )

##TODO: recursive-merge *SysConfig and *Config to a single *Config here (last-in-the-list-wins)
##      (at present *SysConfig is just used as *Config...)

(if (= *Command "rotate-logs")

# Rotate logs

    (let (files
          (mapcar pack
                  (filter '((X) (= (tail 4 X) '("." "l" "o" "g")))
                          (mapcar chop
                                  (dir *LogDir) ) ) ) )
      (if (filter not
                  (mapcar '((X)
                             (let (logfile
                                   (pack *LogDir "/" X)
                                   lockfile
                                   (pack logfile ".lock") )
                               (acquire lockfile)
                               (let (modstamp
                                     (tail 1 (info logfile))
                                     destfile
                                     (pack logfile "."
                                           (dat$ (car modstamp))
                                           (filter '((X) (not (= X ":")))
                                                   (chop (tim$ (cdr modstamp) T)) ) ) )
                                 (call "mv" logfile destfile)
                                 (call "gzip" "-6" destfile) )
                               (release lockfile)
                               T ) )
                           files ) )
          (quit "Rotating one or more of the logfiles finished abnormally" files) ) )

# Server

##TODO: Define this by its differences from the standard http lib using (patch) - to make this much
##      smaller - rather than redefining the entire (http) function using (de) like below...

  (undef 'http)
  (de http (S)
      (use (*Post L @U @H @X)
           (off *Post *Port% *ContLen *Cookies "*Cookies" "*HtSet")
           (catch "http"
             (in S
                 (cond
                  ((not (setq L (line)))
                   (task (close S))
                   (off S)
                   (throw "http") )

# Simple update-protocol is injected here before start of HTTP processing (easier to write bots for).
# Client sends "STATUS\n[uid]\n[status]\n" (\n, not \r\n)

                  ((match '("S" "T" "A" "T" "U" "S") L)
                   (let (uid (in S (line T)) msg (in S (line T)))
                     (if (index uid *Names)
                         (prog
                          (acquire (pack *LogDir "/" uid ".log.lock"))
                          (out (pack "+" *LogDir "/" uid ".log") (prinl (stamp) "|" msg) (flush))
                          (release (pack *LogDir "/" uid ".log.lock"))
                          (out S (prinl "OK") (flush)) ) )
                     (task (close S))
                     (off S)
                     (throw "http") ) )
                  ((match '("G" "E" "T" " " "/" @U " " "H" "T" "T" "P" "/" "1" "." @H) L)
                   (_htHead) )
                  ((match '("P" "O" "S" "T" " " "/" @U " " "H" "T" "T" "P" "/" "1" "." @H) L)
                   (on *Post)
                   (off *MPartLim *MPartEnd)
                   (_htHead)
                   (cond
                    (*MPartLim (_htMultipart))
                    ((if *ContLen (ht:Read @) (line))
                     (for L (split @ '&)
                          (when (cdr (setq L (split L "=")))
                            (let? S (_htSet (car L) (ht:Pack (cadr L)))
                                  (and
                                   (cddr L)
                                   (format (car @))
                                   (unless (out (tmp S) (echo @))
                                     (call 'rm "-f" (tmp S)) ) ) ) ) ) )
                    (T (throw "http")) ) )
                  (T
                   (out S
                        (if
                            (and
                             (match '(@U " " @ " " "H" "T" "T" "P" . @) L)
                             (member @U
                                     (quote
                                      ("O" "P" "T" "I" "O" "N" "S")
                                      ("H" "E" "A" "D")
                                      ("P" "U" "T")
                                      ("D" "E" "L" "E" "T" "E")
                                      ("T" "R" "A" "C" "E")
                                      ("C" "O" "N" "N" "E" "C" "T") ) ) )
                            (httpStat 501 "Method Not Implemented" "Allow: GET, POST")
                          (httpStat 400 "Bad Request") ) )
                   (task (close S))
                   (off S)
                   (throw "http") ) )
                 (if (<> *ConId *SesId)
                     (if *ConId
                         (out S (http404))
                       (task (close S))
                       (off S) )
                   (setq
                    L (split @U "?")
                    @U (car L)
                    L (extract
                       '((L)
                         (cond
                          ((cdr (setq L (split L "=")))
                           (_htSet (car L) (htArg (cadr L)))
                           NIL )
                          ((tail '`(chop ".html") (car L))
                           (pack (car L)) )
                          (T (htArg (car L))) ) )
                       (split (cadr L) "&") ) )
                   (unless (setq *Url (ht:Pack @U))
                     (setq  *Url (car *Home)  @U (cdr *Home)) )

## TODO: If POST then update data, otherwise GET, which follows (eventually could be full REST).
## TODO: Store var-assignment-time and use (info [filename]) to only source a file if it is newer
##       than last var-assignment, otherwise keep existing (caching)

                   (let (statusesByUser
                         (make
                          (for name *Names
                               (let (fileName (pack *LogDir "/" name ".log"))
                                 (if (info fileName)
                                     (ctl (pack "+" *LogDir "/" name ".log.lock")
                                          (in fileName
                                              (chain (list
                                                      (list
                                                       (sym name)
                                                       (by car '((dateStamp) (reverse (sort dateStamp)))
                                                           (make
                                                            (until (eof)
                                                                   (chain (list (mapcar pack (split (chop (line T)) "|")))) ) ) ) ) ) ) ) ) ) ) ) ) )
                     (let (latestStatusByUser
                           (by cadr '((dateStamp) (reverse (sort dateStamp)))
                               (mapcar '((userData)
                                         (list (car userData) (car (last userData))) ) statusesByUser ) )
                           statusesByTime
                           (by car '((dateStamp) (reverse (sort dateStamp)))
                               (make
                                (mapcar '((userData)
                                          (chain
                                           (mapcar '((userStatus)
                                                     (list (car userStatus) (list (car userData) (last userStatus))) ) (last userData) ) ) ) statusesByUser ) ) ) )
                       (out S
                            (cond

## TODO: full interactive web-app, using jquery live updating, integrated DB, etc (see other file)

## TODO: json output
##                          ((tail '("." "j" "s" "o" "n") @U) )

                             ((tail '("." "x" "m" "l") @U)
                              (httpHead "application/xml" 0 NIL NIL)
                              (xml? T)
                              (prinl
                               (xml
                                (list
                                 'Statuses
                                 NIL
                                 (cons
                                  'statusesByUser
                                  NIL
                                  (mapcar '((user)
                                            (cons
                                             'user
                                             (list (cons 'name (car user)))
                                             (mapcar '((status)
                                                       (list
                                                        'status
                                                        (list (cons 'date (car status)))
                                                        (last status) ) ) (last user) ) ) ) statusesByUser ) )
                                 (cons
                                  'latestStatusByUser
                                  NIL
                                  (mapcar '((user)
                                            (list
                                             'user
                                             (list (cons 'name (car user)))
                                             (list
                                              'status
                                              (list (cons 'date (caadr user)))
                                              (last (cadr user)) ) ) ) latestStatusByUser ) )
                                 (cons
                                  'statusesByTime
                                  NIL
                                  (mapcar '((status)
                                            (list
                                             'status
                                             (list (cons 'timestamp (car status)) (cons 'name (caadr status)))
                                             (last (cadr status)) ) ) statusesByTime ) ) ) 2 ) ) )
                             ((tail '("." "l") @U)
                              (httpHead "application/X-lisp" 0 NIL NIL)
                              (pretty (list "statusesByUser" statusesByUser))
                              (prinl) (prinl)
                              (pretty (list "latestStatusByUser" latestStatusByUser))
                              (prinl) (prinl)
                              (pretty (list "statusesByTime" statusesByTime))
                              (prinl) (prinl) )
                             (T
                              (html 0 "Statuses" NIL NIL
                                    (<h1> NIL "Statuses")
                                    (<h2> NIL "Latest status per user")
                                    (<ul> NIL
                                          (mapcar '((user)
                                                    (let (name (car user)
                                                               date (caadr user)
                                                               message (last (cadr user)) )
                                                      (<li> NIL name " => " date " => " message) ) ) latestStatusByUser ) )
                                    (<h2> NIL "All statuses")
                                    (<ul> NIL
                                          (mapcar '((status)
                                                    (let (name (car status)
                                                               date (caadr status)
                                                               message (last (cadr status)) )
                                                      (<li> NIL name " => " date " => " message) ) ) statusesByTime ) )
                                    (<h2> NIL "Statuses by User")
                                    (mapcar '((user)
                                              (let (name (car user)
                                                         statuses (last user) )
                                                (<h3> NIL name)
                                                (<ul> NIL
                                                      (mapcar '((status)
                                                                (let (date (car status)
                                                                           message (last status) )
                                                                  (<li> NIL date " => " message) ) ) statuses ) ) ) ) statusesByUser ) ) ) ) ) ) ) ) ) )
           (and S (=0 *Http1) (task (close S))) ) )
  (call "mkdir" "-p" *LogDir)
  (server *Port ".") )

(bye)
