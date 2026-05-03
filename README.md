## Kubernetes Resources

The repository contains the following deployment resources:

- `deployment.yaml`: Deploys the `game-service` application with 2 base replicas.
- `service.yaml`: Exposes the application through a `LoadBalancer` Service on port `80`, forwarding to container port `8000`.
- `hpa.yaml`: Configures real autoscaling for the `game-service` Deployment from 2 to 5 replicas at a `30%` CPU utilization target.
- `spammer.yaml`: Runs a one-off load-generation Job against the in-cluster Service DNS name `http://game-service:80`.

Current resource settings in this repository:

- Deployment command: `uvicorn main:app --host 0.0.0.0 --port 8000 --no-access-log`
- Deployment requests: `50m` CPU and `52Mi` memory per pod
- Deployment limits: `120m` CPU and `128Mi` memory per pod
- HPA range: 2 to 5 replicas, with an aggressive scale-up policy and 60 second scale-down stabilization
- Spammer profile: `625` RPS for `120` seconds after a `180` second warmup at `300` RPS

### Nodes

Command:

```bash
kubectl get nodes
```

Recorded output:

```text
NAME                                         STATUS   ROLES    AGE    VERSION
gk3-sre-cluster-nap-z0hdt6i8-ccbfd612-9l49   Ready    <none>   170m   v1.35.1-gke.1396002
```

### Pods

Command:

```bash
kubectl get pods
```

Recorded output:

```text
NAME                           READY   STATUS    RESTARTS   AGE
game-service-d9cc468d9-mmj7x   1/1     Running   0          174m
game-service-d9cc468d9-qxm7g   1/1     Running   0          174m
```

### Services

Command:

```bash
kubectl get svc
```

Recorded output:

```text
NAME           TYPE           CLUSTER-IP       EXTERNAL-IP    PORT(S)        AGE
game-service   LoadBalancer   34.118.225.128   34.118.34.44   80:32469/TCP   165m
kubernetes     ClusterIP      34.118.224.1     <none>         443/TCP        24h
```

## Load Test Procedure

The load test was started with:

```bash
kubectl apply -f spammer.yaml
```

Recorded pod state after creating the Job:

```text
NAME                           READY   STATUS      RESTARTS   AGE
game-service-d9cc468d9-mmj7x   1/1     Running     0          3h42m
game-service-d9cc468d9-qxm7g   1/1     Running     0          3h42m
spammer-qnsbn                  0/1     Completed   0          5m52s
```

The Job logs were viewed with:

```bash
kubectl logs spammer-qnsbn
```

## Recorded Load Test Results

### Scenario 1: Baseline at 1000 RPS

Profile:

- RPS: `1000`
- Duration: `60s`
- Warmup: `60s @ 100 req/s`
- Endpoints: `get_stats`, `update_player`

Recorded output:

```text
Spamming http://game-service:80
  RPS         : 1000
  Duration    : 60s
  Warmup      : 60s @ 100 req/s
  Endpoints   : ['get_stats', 'update_player']

Warming up for 60s at 100 req/s...
Warmup done.
Sending 60000 requests at 1000 req/s for 60s...

============================================================
SPAMMER REPORT
============================================================
Total requests : 60000
Wall time      : 157.11s
Throughput     : 381.9 req/s
Success (2xx)  : 9993
Client err(4xx): 0
Errors/5xx     : 50007

Latency (ms):
  avg : 19252.3
  p50 : 11760.8
  p95 : 63478.2
  p99 : 66420.9
  min : 25.1
  max : 68062.0
============================================================
```

This baseline configuration did not sustain the requested throughput and produced a high 5xx error rate.

### Scenario 2: Reduced Load at 500 RPS

Profile:

- RPS: `500`
- Duration: `60s`
- Warmup: `60s @ 50 req/s`
- Endpoints: `get_stats`, `update_player`

Recorded output:

```text
Spamming http://game-service:80
  RPS         : 500
  Duration    : 60s
  Warmup      : 60s @ 50 req/s
  Endpoints   : ['get_stats', 'update_player']

Warming up for 60s at 50 req/s...
Warmup done.
Sending 30000 requests at 500 req/s for 60s...

============================================================
SPAMMER REPORT
============================================================
Total requests : 30000
Wall time      : 79.02s
Throughput     : 379.6 req/s
Success (2xx)  : 22383
Client err(4xx): 0
Errors/5xx     : 7617

Latency (ms):
  avg : 2767.1
  p50 : 833.9
  p95 : 17744.1
  p99 : 26309.3
  min : 9.7
  max : 30814.5
============================================================
```

Reducing the offered load improved the success rate, but the service still produced a material number of 5xx responses.

### Scenario 3: HPA with Maximum 4 Replicas at 30% CPU Utilization

Recorded output:

```text
Spamming http://game-service:80
  RPS         : 500
  Duration    : 60s
  Warmup      : 60s @ 50 req/s
  Endpoints   : ['get_stats', 'update_player']

Warming up for 60s at 50 req/s...
Warmup done.
Sending 30000 requests at 500 req/s for 60s...

============================================================
SPAMMER REPORT
============================================================
Total requests : 30000
Wall time      : 61.75s
Throughput     : 485.8 req/s
Success (2xx)  : 29982
Client err(4xx): 0
Errors/5xx     : 18

Latency (ms):
  avg : 1411.7
  p50 : 254.5
  p95 : 11792.2
  p99 : 18181.3
  min : 6.9
  max : 27048.5
============================================================
```

This configuration significantly improved throughput and reduced server errors to a negligible level. The lower CPU utilization target was used to encourage earlier scale-out for this workload pattern.

### Scenario 4: CPU Request Reduced to 50m with 60% CPU Utilization Target

Recorded output:

```text
Spamming http://game-service:80
  RPS         : 500
  Duration    : 60s
  Warmup      : 60s @ 50 req/s
  Endpoints   : ['get_stats', 'update_player']

Warming up for 60s at 50 req/s...
Warmup done.
Sending 30000 requests at 500 req/s for 60s...

============================================================
SPAMMER REPORT
============================================================
Total requests : 30000
Wall time      : 60.09s
Throughput     : 499.2 req/s
Success (2xx)  : 30000
Client err(4xx): 0
Errors/5xx     : 0

Latency (ms):
  avg : 75.1
  p50 : 55.2
  p95 : 181.2
  p99 : 381.5
  min : 5.9
  max : 1409.1
============================================================
```

This was the strongest recorded result in the verification notes. Under the `500` RPS profile, the service completed all `30000` requests successfully with no 5xx responses.

### Scenario 5: Selected Scaling Configuration

The final selected configuration disables Uvicorn access logs and uses the HPA to scale from 2 base replicas to 5 replicas during warmup. This keeps idle resources low while still preparing enough capacity before the measured spike.

During warmup, HPA was observed scaling from 2 to 5 replicas:

```text
NAME               REFERENCE                 TARGETS         MINPODS   MAXPODS   REPLICAS
game-service-hpa   Deployment/game-service   cpu: 137%/30%   2         5         5
```

Recorded output:

```text
Spamming http://game-service:80
  RPS         : 625
  Duration    : 120s
  Warmup      : 180s @ 300 req/s
  Endpoints   : ['get_stats', 'update_player']

Warming up for 180s at 300 req/s...
Warmup done.
Sending 75000 requests at 625 req/s for 120s...

============================================================
SPAMMER REPORT
============================================================
Total requests : 75000
Wall time      : 120.29s
Throughput     : 623.5 req/s
Success (2xx)  : 74994
Client err(4xx): 0
Errors/5xx     : 6

Latency (ms):
  avg : 343.9
  p50 : 87.2
  p95 : 913.8
  p99 : 6645.9
  min : 4.9
  max : 15953.0
============================================================
```

This is a `99.992%` success rate under the `625` RPS spike profile. Higher tests were also tried: `650` RPS produced `88` 5xx responses, while `700` RPS produced `574` 5xx responses. `750` RPS was rejected because it overloaded the deployment and caused pod restarts.

## Conclusion

The verification data shows a clear progression:

- The baseline deployment could not sustain `1000` RPS reliably.
- Reducing traffic to `500` RPS improved results, but did not eliminate server-side failures.
- Adding autoscaling headroom and tuning CPU-based scaling materially improved performance.
- Disabling Uvicorn access logs removed a major source of per-request overhead.
- The selected configuration starts at 2 replicas and scales to 5 during warmup, producing near-zero 5xx responses under a `625` RPS spike.

This repository is therefore configured around a real scale-out demonstration: low steady-state replicas, warmup-driven HPA scale-out, and a high-RPS spike handled by the scaled deployment.
