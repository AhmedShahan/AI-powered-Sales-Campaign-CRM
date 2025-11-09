#!/bin/bash
# Wait for MailHog to be ready

echo "Waiting for MailHog to be ready..."
until nc -z mailhog 1025; do
  echo "MailHog is not ready yet. Waiting..."
  sleep 2
done
echo "MailHog is ready!"

exec "$@"

