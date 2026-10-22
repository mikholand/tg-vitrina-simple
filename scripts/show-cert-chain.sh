#!/bin/sh
echo | openssl s_client -connect 127.0.0.1:443 -servername alenazhao.ru -showcerts 2>/dev/null |
  awk '/BEGIN CERTIFICATE/,/END CERTIFICATE/{print}' |
  csplit -s -f /tmp/le-cert- - '/-----BEGIN CERTIFICATE-----/' '{*}' >/dev/null 2>&1
n=0
for f in /tmp/le-cert-*; do
  [ -s "$f" ] || continue
  n=$((n + 1))
  echo "--- cert $n ---"
  openssl x509 -in "$f" -noout -subject -issuer
done
echo "total=$n"
