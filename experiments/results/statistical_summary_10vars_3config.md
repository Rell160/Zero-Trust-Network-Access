# Summary of Experimental Measurements

|                     |   sample_size |   auth_latency_mean_ms |   auth_latency_std_ms |   pdp_latency_mean_ms |   pdp_latency_std_ms |   pdp_latency_ci95 |   mfa_response_time_mean_ms |   accuracy_percent |   far_percent |   frr_percent |   unauthorized_prevention_rate_percent |   adaptation_time_mean_ms |   cpu_utilization_mean_percent |   ram_utilization_mean_mb |
|:--------------------|--------------:|-----------------------:|----------------------:|----------------------:|---------------------:|-------------------:|----------------------------:|-------------------:|--------------:|--------------:|---------------------------------------:|--------------------------:|-------------------------------:|--------------------------:|
| baseline_vpn        |          3000 |                 10     |                 0     |                 0     |                0     |                  0 |                       0     |              60.47 |        100    |             0 |                                   0    |                     0     |                           1.39 |                    146.97 |
| static_mfa          |          3000 |                 25     |                 0     |                 0     |                0     |                  0 |                      15     |              60.47 |         62.73 |             0 |                                  37.27 |                     0     |                           0.62 |                    146.97 |
| proposed_risk_aware |          3000 |                  0.108 |                 0.151 |                 0.013 |                0.012 |                  0 |                       4.338 |              75.2  |         62.73 |             0 |                                  37.27 |                     0.121 |                           1.02 |                    146.97 |

## Hypothesis Testing

- **Test Executed**: Mann-Whitney U test
- **Statistic**: 8999193.000
- **p-value**: 0.00000e+00
- **Significant (p < 0.05)**: True
