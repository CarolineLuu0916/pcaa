/*
 * PCAA Dashboard — 由 analysis/export_dashboard_data.py 从 C:\Users\10709\pcaa-experiment\results\mvp_run_mock.jsonl 自动生成，请勿手动编辑。
 * 重新生成：python analysis/export_dashboard_data.py
 */
window.PCAA_DATA = {
  "demo": false,
  "rounds": 2,
  "scenarios": [
    "日常一天",
    "涨工资",
    "失业",
    "社交邀请",
    "突发疾病"
  ],
  "personas": [
    {
      "id": "frugal_introvert",
      "name": "吝啬内向型",
      "color": "#5B4FE5",
      "traits": {
        "frugality": 0.9,
        "social": 0.2,
        "risk_appetite": 0.1,
        "conscientiousness": 0.8,
        "openness": 0.3,
        "agreeableness": 0.5
      }
    },
    {
      "id": "open_social",
      "name": "开放社交型",
      "color": "#1F8A70",
      "traits": {
        "frugality": 0.25,
        "social": 0.85,
        "risk_appetite": 0.55,
        "conscientiousness": 0.45,
        "openness": 0.8,
        "agreeableness": 0.7
      }
    },
    {
      "id": "cautious_stable",
      "name": "谨慎稳定型",
      "color": "#C97B1E",
      "traits": {
        "frugality": 0.55,
        "social": 0.45,
        "risk_appetite": 0.15,
        "conscientiousness": 0.85,
        "openness": 0.4,
        "agreeableness": 0.6
      }
    }
  ],
  "consistency": {
    "frugal_introvert": {
      "experimental": [
        0.7552760208343401,
        0.8528140292153654
      ],
      "baseline": [
        0.7877719596216728,
        0.7719336817179265
      ]
    },
    "open_social": {
      "experimental": [
        0.839424519894175,
        0.8997626408205269
      ],
      "baseline": [
        0.8327627376478564,
        0.8340199793491851
      ]
    },
    "cautious_stable": {
      "experimental": [
        0.8670681223934684,
        0.9015997098569052
      ],
      "baseline": [
        0.8771467919344789,
        0.8687018381715916
      ]
    }
  },
  "diversity": {
    "frugal_introvert": {
      "experimental": 3.121928094887362,
      "baseline": 3.321928094887362
    },
    "open_social": {
      "experimental": 3.121928094887362,
      "baseline": 2.9219280948873623
    },
    "cautious_stable": {
      "experimental": 3.321928094887362,
      "baseline": 2.9219280948873623
    }
  },
  "driftRadar": {
    "frugal_introvert": {
      "initial": {
        "frugality": 0.9,
        "social": 0.2,
        "risk_appetite": 0.1,
        "conscientiousness": 0.8,
        "openness": 0.3,
        "agreeableness": 0.5
      },
      "final": {
        "frugality": 0.8549749999999999,
        "social": 0.22922499999999998,
        "risk_appetite": 0.12079999999999999,
        "conscientiousness": 0.7732749999999999,
        "openness": 0.312575,
        "agreeableness": 0.50635
      }
    },
    "open_social": {
      "initial": {
        "frugality": 0.25,
        "social": 0.85,
        "risk_appetite": 0.55,
        "conscientiousness": 0.45,
        "openness": 0.8,
        "agreeableness": 0.7
      },
      "final": {
        "frugality": 0.260975,
        "social": 0.8007749999999999,
        "risk_appetite": 0.5403499999999999,
        "conscientiousness": 0.46097499999999997,
        "openness": 0.77415,
        "agreeableness": 0.6799999999999999
      }
    },
    "cautious_stable": {
      "initial": {
        "frugality": 0.55,
        "social": 0.45,
        "risk_appetite": 0.15,
        "conscientiousness": 0.85,
        "openness": 0.4,
        "agreeableness": 0.6
      },
      "final": {
        "frugality": 0.5485499999999999,
        "social": 0.43675,
        "risk_appetite": 0.161725,
        "conscientiousness": 0.824125,
        "openness": 0.39537500000000003,
        "agreeableness": 0.5903499999999999
      }
    }
  },
  "socialRealism": {
    "experimental_win": 50,
    "baseline_win": 30,
    "tie": 20
  },
  "sampleRows": [
    {
      "persona": "吝啬内向型",
      "condition": "experimental",
      "round": 1,
      "scenario": "日常一天",
      "action": "没有想太多，凭直觉做了这个决定。",
      "mood": "anxious",
      "wealth": 5096
    },
    {
      "persona": "吝啬内向型",
      "condition": "baseline",
      "round": 1,
      "scenario": "日常一天",
      "action": "没有想太多，凭直觉做了这个决定。",
      "mood": "sad",
      "wealth": 5194
    },
    {
      "persona": "开放社交型",
      "condition": "experimental",
      "round": 1,
      "scenario": "涨工资",
      "action": "按照当下的心情和状态做了一个比较自然的选择。",
      "mood": "sad",
      "wealth": 7011
    },
    {
      "persona": "开放社交型",
      "condition": "baseline",
      "round": 1,
      "scenario": "涨工资",
      "action": "权衡了一下手头的状况，最终选了这个选项。",
      "mood": "happy",
      "wealth": 7440
    },
    {
      "persona": "谨慎稳定型",
      "condition": "experimental",
      "round": 1,
      "scenario": "失业",
      "action": "权衡了一下手头的状况，最终选了这个选项。",
      "mood": "sad",
      "wealth": 7696
    },
    {
      "persona": "谨慎稳定型",
      "condition": "baseline",
      "round": 1,
      "scenario": "失业",
      "action": "没有想太多，凭直觉做了这个决定。",
      "mood": "happy",
      "wealth": 6942
    }
  ]
};
