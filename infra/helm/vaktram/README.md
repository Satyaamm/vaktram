# Vaktram Helm chart

Deploys the API, web, bot, transcribe / summarize / diarize workers, optional
Postgres + Redis, and Prometheus alerting rules.

## SaaS install (default)

```bash
helm install vaktram ./vaktram \
  -f values.yaml \
  --set global.imageTag=$VERSION \
  --set api.env.JWT_SECRET=$JWT_SECRET \
  --set api.env.STRIPE_API_KEY=$STRIPE_API_KEY
```

## EU residency

```bash
helm install vaktram-eu ./vaktram -f values.yaml -f values-eu.yaml
```

## On-prem / VPC (air-gapped friendly)

```bash
helm install vaktram ./vaktram -f values.yaml -f values-onprem.yaml
```

The on-prem values bundle Postgres + Redis inside the cluster and disable the
managed-ingress assumptions so the customer can route through their own LB.
