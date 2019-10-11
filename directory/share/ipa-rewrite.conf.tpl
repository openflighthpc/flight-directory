# VERSION 6 - DO NOT REMOVE THIS LINE
#==============================================================================
# Copyright (C) 2019-present Alces Flight Ltd.
#
# This file is part of Flight Directory.
#
# This program and the accompanying materials are made available under
# the terms of the Eclipse Public License 2.0 which is available at
# <https://www.eclipse.org/legal/epl-2.0>, or alternative license
# terms made available by Alces Flight Ltd - please direct inquiries
# about licensing to licensing@alces-flight.com.
#
# Flight Directory is distributed in the hope that it will be useful, but
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESS OR
# IMPLIED INCLUDING, WITHOUT LIMITATION, ANY WARRANTIES OR CONDITIONS
# OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A
# PARTICULAR PURPOSE. See the Eclipse Public License 2.0 for more
# details.
#
# You should have received a copy of the Eclipse Public License 2.0
# along with Flight Directory. If not, see:
#
#  https://opensource.org/licenses/EPL-2.0
#
# For more information on Flight Directory, please visit:
# https://github.com/openflighthpc/flight-directory
#==============================================================================
# vim: set filetype=apache :

RewriteEngine on

# By default forward all requests to /ipa. If you don't want IPA
# to be the default on your web server comment this line out.
RewriteRule ^/$ /ipa/ui [L,NC,R=302]

# Redirect to the fully-qualified hostname. Not redirecting to secure
# port so configuration files can be retrieved without requiring SSL.
# We only do this if the request is from inside the VPC.
RewriteCond %{REMOTE_ADDR} ^_ESCAPED-DOMAIN-NETWORK-PREFIX_
RewriteCond %{HTTP_HOST} !^_INTERNAL-NAME_$ [NC]
RewriteRule ^/ipa/(.*) http://_INTERNAL-NAME_/ipa/$1 [L,R=302]

# Redirect direct HTTP requests from outside the VPC to the external hostname.
RewriteCond %{REMOTE_ADDR} !^_ESCAPED-DOMAIN-NETWORK-PREFIX_
RewriteCond %{REMOTE_ADDR} !^127\.0\.0\.1$
RewriteCond %{HTTP_HOST} !^_ESCAPED-EXTERNAL-NAME_$ [NC]
RewriteRule ^/(.*) http://_EXTERNAL-NAME_/$1 [L,R=302]

# Redirect to the secure port if not displaying an error or retrieving
# configuration.
# We only do this if the request is not from the localhost proxy.
RewriteCond %{SERVER_PORT}  !^443$
RewriteCond %{REQUEST_URI}  !^/ipa/(errors|config|crl)
RewriteCond %{REQUEST_URI}  !^/ipa/[^\?]+(\.js|\.css|\.png|\.gif|\.ico|\.woff|\.svg|\.ttf|\.eot)$
RewriteCond %{HTTP_HOST}    !^127\.0\.0\.1$
RewriteRule ^/ipa/(.*)      https://%{HTTP_HOST}/ipa/$1 [L,R=302,NC]

# Rewrite for plugin index, make it like it's a static file
RewriteRule ^/ipa/ui/js/freeipa/plugins.js$    /ipa/wsgi/plugins.py [PT]
