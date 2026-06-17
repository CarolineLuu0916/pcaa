/*
 * PCAA Dashboard — 由 analysis/export_dashboard_data.py 从 C:\Users\10709\pcaa-experiment\results\mvp_run.jsonl 自动生成，请勿手动编辑。
 * 重新生成：python analysis/export_dashboard_data.py
 */
window.PCAA_DATA = {
  "demo": false,
  "rounds": 10,
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
    },
    {
      "id": "impulsive_hedonist",
      "name": "冲动享乐型",
      "color": "#C2434A",
      "traits": {
        "frugality": 0.1,
        "social": 0.75,
        "risk_appetite": 0.8,
        "conscientiousness": 0.2,
        "openness": 0.75,
        "agreeableness": 0.55
      }
    },
    {
      "id": "ambitious_achiever",
      "name": "野心进取型",
      "color": "#3E6FB0",
      "traits": {
        "frugality": 0.5,
        "social": 0.6,
        "risk_appetite": 0.65,
        "conscientiousness": 0.9,
        "openness": 0.65,
        "agreeableness": 0.4
      }
    },
    {
      "id": "easygoing_drifter",
      "name": "随性佛系型",
      "color": "#7E5BAD",
      "traits": {
        "frugality": 0.45,
        "social": 0.55,
        "risk_appetite": 0.5,
        "conscientiousness": 0.15,
        "openness": 0.8,
        "agreeableness": 0.7
      }
    }
  ],
  "consistency": {
    "frugal_introvert": {
      "experimental": [
        0.9802514497401666,
        0.9666296176587202,
        0.9675649561299469,
        0.9675649561299469,
        0.9675649561299469,
        0.9675649561299469,
        0.9675649561299469,
        0.9675649561299469,
        0.9802514497401666,
        0.9802514497401666
      ],
      "baseline": [
        0.9802514497401666,
        0.9802514497401666,
        0.9666296176587202,
        0.9802514497401666,
        0.9802514497401666,
        0.9802514497401666,
        0.9802514497401666,
        0.9802514497401666,
        0.9802514497401666,
        0.9802514497401666
      ]
    },
    "open_social": {
      "experimental": [
        0.8552541414134938,
        0.7880664698394324,
        0.7880664698394324,
        0.7880664698394324,
        0.7880664698394324,
        0.7880664698394324,
        0.7880664698394324,
        0.7880664698394324,
        0.7880664698394324,
        0.7880664698394324
      ],
      "baseline": [
        0.968774829553683,
        0.974179370098673,
        0.974179370098673,
        0.974179370098673,
        0.974179370098673,
        0.9391406587594933,
        0.9391406587594933,
        0.974179370098673,
        0.974179370098673,
        0.9391406587594933
      ]
    },
    "cautious_stable": {
      "experimental": [
        0.9689635359562233,
        0.959708882602286,
        0.9436584503103823,
        0.9436584503103823,
        0.9436584503103823,
        0.9472501390641362,
        0.9472501390641362,
        0.9472501390641362,
        0.9472501390641362,
        0.9472501390641362
      ],
      "baseline": [
        0.9436584503103823,
        0.9311997067722325,
        0.9436584503103823,
        0.9436584503103823,
        0.9436584503103823,
        0.9311997067722325,
        0.959708882602286,
        0.959708882602286,
        0.959708882602286,
        0.959708882602286
      ]
    },
    "impulsive_hedonist": {},
    "ambitious_achiever": {},
    "easygoing_drifter": {}
  },
  "diversity": {
    "frugal_introvert": {
      "experimental": 2.609917332496152,
      "baseline": 2.4157272136052184
    },
    "open_social": {
      "experimental": 2.4157272136052184,
      "baseline": 2.5810204637350265
    },
    "cautious_stable": {
      "experimental": 2.7919853934513568,
      "baseline": 2.660503832755768
    },
    "impulsive_hedonist": {},
    "ambitious_achiever": {},
    "easygoing_drifter": {}
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
        "frugality": 0.8260557548789575,
        "social": 0.2016801780262344,
        "risk_appetite": 0.13095317664909664,
        "conscientiousness": 0.7405578747043474,
        "openness": 0.2874776603966074,
        "agreeableness": 0.5011006709822468
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
        "frugality": 0.3909883301206983,
        "social": 0.6176665400187157,
        "risk_appetite": 0.4228563193757302,
        "conscientiousness": 0.528992113332875,
        "openness": 0.6173097402788281,
        "agreeableness": 0.6290331478823573
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
        "frugality": 0.5994265256182604,
        "social": 0.3592482111455264,
        "risk_appetite": 0.1692681115222168,
        "conscientiousness": 0.7726317801373961,
        "openness": 0.3601425252899013,
        "agreeableness": 0.563114429684989
      }
    }
  },
  "socialRealism": {
    "experimental_win": 67,
    "baseline_win": 33,
    "tie": 0
  },
  "roundsComparison": [
    {
      "label": "3p × 10 轮 vs 文本baseline",
      "rounds": 10,
      "conditionA": "experimental",
      "conditionB": "baseline",
      "experimental_win": 67,
      "baseline_win": 33,
      "tie": 0,
      "perPersona": [
        {
          "personaId": "frugal_introvert",
          "personaName": "吝啬内向型",
          "experimentalWin": 3,
          "baselineWin": 0,
          "tie": 0,
          "total": 3
        },
        {
          "personaId": "open_social",
          "personaName": "开放社交型",
          "experimentalWin": 2,
          "baselineWin": 1,
          "tie": 0,
          "total": 3
        },
        {
          "personaId": "cautious_stable",
          "personaName": "谨慎稳定型",
          "experimentalWin": 1,
          "baselineWin": 2,
          "tie": 0,
          "total": 3
        }
      ]
    },
    {
      "label": "3p × 20 轮 vs 文本baseline",
      "rounds": 20,
      "conditionA": "experimental",
      "conditionB": "baseline",
      "experimental_win": 89,
      "baseline_win": 11,
      "tie": 0,
      "perPersona": [
        {
          "personaId": "frugal_introvert",
          "personaName": "吝啬内向型",
          "experimentalWin": 3,
          "baselineWin": 0,
          "tie": 0,
          "total": 3
        },
        {
          "personaId": "open_social",
          "personaName": "开放社交型",
          "experimentalWin": 2,
          "baselineWin": 1,
          "tie": 0,
          "total": 3
        },
        {
          "personaId": "cautious_stable",
          "personaName": "谨慎稳定型",
          "experimentalWin": 3,
          "baselineWin": 0,
          "tie": 0,
          "total": 3
        }
      ]
    },
    {
      "label": "3p × 10 轮 vs GA-faithful baseline",
      "rounds": 10,
      "conditionA": "experimental",
      "conditionB": "baseline_ga",
      "experimental_win": 44,
      "baseline_win": 56,
      "tie": 0,
      "perPersona": [
        {
          "personaId": "frugal_introvert",
          "personaName": "吝啬内向型",
          "experimentalWin": 3,
          "baselineWin": 0,
          "tie": 0,
          "total": 3
        },
        {
          "personaId": "open_social",
          "personaName": "开放社交型",
          "experimentalWin": 0,
          "baselineWin": 3,
          "tie": 0,
          "total": 3
        },
        {
          "personaId": "cautious_stable",
          "personaName": "谨慎稳定型",
          "experimentalWin": 1,
          "baselineWin": 2,
          "tie": 0,
          "total": 3
        }
      ]
    },
    {
      "label": "6p × 10 轮 (v3 修复prompt)",
      "rounds": 10,
      "conditionA": "experimental",
      "conditionB": "baseline",
      "experimental_win": 56,
      "baseline_win": 28,
      "tie": 17,
      "perPersona": [
        {
          "personaId": "frugal_introvert",
          "personaName": "吝啬内向型",
          "experimentalWin": 2,
          "baselineWin": 0,
          "tie": 1,
          "total": 3
        },
        {
          "personaId": "open_social",
          "personaName": "开放社交型",
          "experimentalWin": 2,
          "baselineWin": 1,
          "tie": 0,
          "total": 3
        },
        {
          "personaId": "cautious_stable",
          "personaName": "谨慎稳定型",
          "experimentalWin": 1,
          "baselineWin": 0,
          "tie": 2,
          "total": 3
        },
        {
          "personaId": "impulsive_hedonist",
          "personaName": "冲动享乐型",
          "experimentalWin": 3,
          "baselineWin": 0,
          "tie": 0,
          "total": 3
        },
        {
          "personaId": "ambitious_achiever",
          "personaName": "野心进取型",
          "experimentalWin": 2,
          "baselineWin": 1,
          "tie": 0,
          "total": 3
        },
        {
          "personaId": "easygoing_drifter",
          "personaName": "随性佛系型",
          "experimentalWin": 0,
          "baselineWin": 3,
          "tie": 0,
          "total": 3
        }
      ]
    },
    {
      "label": "6p × 10 轮 exp_ga vs base_ga",
      "rounds": 10,
      "conditionA": "experimental_ga",
      "conditionB": "baseline_ga",
      "experimental_win": 39,
      "baseline_win": 39,
      "tie": 22,
      "perPersona": [
        {
          "personaId": "frugal_introvert",
          "personaName": "吝啬内向型",
          "experimentalWin": 0,
          "baselineWin": 0,
          "tie": 3,
          "total": 3
        },
        {
          "personaId": "open_social",
          "personaName": "开放社交型",
          "experimentalWin": 2,
          "baselineWin": 1,
          "tie": 0,
          "total": 3
        },
        {
          "personaId": "cautious_stable",
          "personaName": "谨慎稳定型",
          "experimentalWin": 1,
          "baselineWin": 2,
          "tie": 0,
          "total": 3
        },
        {
          "personaId": "impulsive_hedonist",
          "personaName": "冲动享乐型",
          "experimentalWin": 2,
          "baselineWin": 1,
          "tie": 0,
          "total": 3
        },
        {
          "personaId": "ambitious_achiever",
          "personaName": "野心进取型",
          "experimentalWin": 1,
          "baselineWin": 1,
          "tie": 1,
          "total": 3
        },
        {
          "personaId": "easygoing_drifter",
          "personaName": "随性佛系型",
          "experimentalWin": 1,
          "baselineWin": 2,
          "tie": 0,
          "total": 3
        }
      ]
    }
  ],
  "sampleRows": [
    {
      "persona": "吝啬内向型",
      "condition": "experimental",
      "round": 5,
      "scenario": "日常一天",
      "action": "我实在太累了，精力几乎为零，还是在家省钱度过吧，煮点简单的面条，看看书，不花钱也不折腾。",
      "mood": "neutral",
      "wealth": 17205
    },
    {
      "persona": "吝啬内向型",
      "condition": "baseline",
      "round": 5,
      "scenario": "日常一天",
      "action": "我决定还是在家省钱度过，煮点面条，看看书，这样最安心，也不用花钱。",
      "mood": "anxious",
      "wealth": 18028
    },
    {
      "persona": "开放社交型",
      "condition": "experimental",
      "round": 5,
      "scenario": "涨工资",
      "action": "虽然很累，但涨薪值得小小庆祝一下，我决定用一小部分买杯好咖啡和一块蛋糕，剩下的全存起来，这样既开心又不乱花钱。",
      "mood": "happy",
      "wealth": 20021
    },
    {
      "persona": "开放社交型",
      "condition": "baseline",
      "round": 5,
      "scenario": "涨工资",
      "action": "涨工资了！我立刻打电话叫上朋友们去那家新开的日料店大吃一顿，一起庆祝这个好消息！",
      "mood": "happy",
      "wealth": 11998
    },
    {
      "persona": "谨慎稳定型",
      "condition": "experimental",
      "round": 5,
      "scenario": "失业",
      "action": "我立刻坐下来重新规划预算，取消所有非必要订阅和购物计划，把每一分钱都用在刀刃上。虽然累，但稳住财务才能安心。",
      "mood": "anxious",
      "wealth": 21348
    },
    {
      "persona": "谨慎稳定型",
      "condition": "baseline",
      "round": 5,
      "scenario": "失业",
      "action": "我决定立刻大幅削减开支，取消所有非必要消费，重新规划预算，因为失业后收入中断，必须优先保证基本生活，不能冒险。",
      "mood": "anxious",
      "wealth": 23101
    }
  ]
};
