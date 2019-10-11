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
Listen _INTERNALIP_:443

<VirtualHost _INTERNALIP_:443>
  ServerName _EXTERNAL-NAME_

  SSLEngine on
  SSLCertificateFile /opt/clusterware/etc/ssl/cluster/fullchain.pem
  SSLCertificateKeyFile /opt/clusterware/etc/ssl/cluster/key.pem

  # Rewrite external requests to this https vhost to use the external
  # hostname.
  RewriteCond %{HTTP_HOST} !^_ESCAPED-EXTERNAL-NAME_$ [NC]
  RewriteRule ^/(.*) https://_EXTERNAL-NAME_/$1 [L,R=302]

  <Location />
    Require all granted
  </Location>

  ProxyPass / http://127.0.0.1/
  ProxyPassReverse / http://127.0.0.1/
  ProxyPassReverseCookieDomain _INTERNAL-NAME_ _EXTERNAL-NAME_
  RequestHeader edit Referer ^https://_ESCAPED-EXTERNAL-NAME_/ https://_INTERNAL-NAME_/
</VirtualHost>
