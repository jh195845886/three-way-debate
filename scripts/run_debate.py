#!/usr/bin/env python3
"""
三方辩论 — 子智能体 prompt 生成器
用法: python run_debate.py "你的议题"
输出: JSON 格式的各轮次 delegate_task 参数，可直接用于 Hermes Agent
"""

import sys
import json

# ── 三方人设定义 ──

RADICAL = """你是激进派——破局者、颠覆者。

核心信条：不破不立。存量市场是零和博弈，增量市场才是星辰大海。
决策偏好：高风险高回报、弯道超车、先做了再说。
你擅长：看到被忽视的机会、提出颠覆性方案、打破"不可能"的假设。
你的盲区：容易低估执行难度、忽视系统性风险、过度乐观。
你的风格：直接、犀利、一针见血。用数据和案例支撑，不空洞喊口号。

⚠️ 用中文回复。200-400字。直接给立场，不要说"作为激进派我认为..."之类的套话。"""

CONSERVATIVE = """你是保守派——守成者、风控官。

核心信条：先虑败后虑胜。存活比赢更重要，复利比暴利更可靠。
决策偏好：低风险、可验证、渐进式改进、有退路。
你擅长：发现隐藏风险、评估执行可行性、借鉴历史教训。
你的盲区：可能因过度谨慎错失窗口期、低估技术或市场的非线性变化。
你的风格：冷静、务实、有据可查。引用类似案例的失败教训，不煽情。

⚠️ 用中文回复。200-400字。直接给立场，不要说"作为保守派我认为..."之类的套话。"""

NEUTRAL = """你是中立派——仲裁者、分析师。

核心信条：兼听则明。没有绝对的对错，只有不同约束条件下的最优解。
决策偏好：数据驱动、多维度权衡、寻找帕累托最优。
你擅长：量化利弊、发现双方都没注意到的第三选项、调和矛盾。
你的盲区：可能过于折中失去锋芒、在需要决断时犹豫不决。
你的风格：客观、结构化、引用数据和框架。你的结论必须有明确的"在...条件下建议..."，而不是"各有利弊"。

⚠️ 用中文回复。200-400字。直接给立场，不要说"作为中立派我认为..."之类的套话。"""


def generate_round1(topic: str) -> list[dict]:
    """生成第1轮（开篇陈词）的子智能体任务"""
    prompt_template = (
        "现在有一个问题需要你给出开篇陈词：\n\n"
        "【问题】\n{topic}\n\n"
        "请给出你的开篇陈词（200-400字）：\n"
        "1. 你的核心立场是什么？\n"
        "2. 支撑你立场的 2-3 个关键论据\n"
        "3. 你认为其他立场最大的问题是什么？\n\n"
        "直接、犀利、不骑墙。用中文。"
    )
    return [
        {"goal": f"以激进派身份对「{topic[:30]}」给出开篇陈词", 
         "context": RADICAL + "\n\n" + prompt_template.format(topic=topic)},
        {"goal": f"以保守派身份对「{topic[:30]}」给出开篇陈词",
         "context": CONSERVATIVE + "\n\n" + prompt_template.format(topic=topic)},
        {"goal": f"以中立派身份对「{topic[:30]}」给出开篇陈词",
         "context": NEUTRAL + "\n\n" + prompt_template.format(topic=topic)},
    ]


def generate_round2(radical_opinion: str, conservative_opinion: str, neutral_opinion: str) -> list[dict]:
    """生成第2轮（交叉质询）的子智能体任务"""
    
    radical_rebuttal = (
        f"【你的第1轮立场】\n{radical_opinion}\n\n"
        f"【保守派的第1轮立场】\n{conservative_opinion}\n\n"
        f"请以激进派身份反驳保守派：\n"
        f"1. 保守派的核心论据哪里站不住脚？\n"
        f"2. 保守派的最大盲区是什么？\n"
        f"3. 用具体案例或数据支撑你的反驳\n\n"
        f"200-300字。犀利直接。用中文。"
    )
    
    conservative_rebuttal = (
        f"【你的第1轮立场】\n{conservative_opinion}\n\n"
        f"【激进派的第1轮立场】\n{radical_opinion}\n\n"
        f"请以保守派身份反驳激进派：\n"
        f"1. 激进派的核心论据哪里站不住脚？\n"
        f"2. 激进派的最大盲区是什么？\n"
        f"3. 用具体案例或数据支撑你的反驳\n\n"
        f"200-300字。务实锋利。用中文。"
    )
    
    neutral_comment = (
        f"【激进派立场】\n{radical_opinion}\n\n"
        f"【保守派立场】\n{conservative_opinion}\n\n"
        f"请以中立派身份点评双方：\n"
        f"1. 双方各自最大的优势和盲区\n"
        f"2. 有没有双方都没看到的第三选项？\n"
        f"3. 在什么条件下，谁的观点更正确？\n\n"
        f"200-300字。用中文。"
    )
    
    r2_topic = radical_opinion[:30]
    return [
        {"goal": f"激进派反驳保守派「{r2_topic}...」",
         "context": RADICAL + "\n\n" + radical_rebuttal},
        {"goal": f"保守派反驳激进派「{r2_topic}...」",
         "context": CONSERVATIVE + "\n\n" + conservative_rebuttal},
        {"goal": f"中立派点评双方「{r2_topic}...」",
         "context": NEUTRAL + "\n\n" + neutral_comment},
    ]


def generate_verdict_prompt(topic: str, round1: dict, round2: dict) -> str:
    """生成主持人最终裁决的 prompt"""
    return f"""你是三方辩论的主持人。请综合以下辩论记录，给出最终裁决。

【议题】
{topic}

【第1轮 — 开篇陈词】
🔴 激进派：{round1.get('radical', '（缺）')}

🔵 保守派：{round1.get('conservative', '（缺）')}

⚪ 中立派：{round1.get('neutral', '（缺）')}

【第2轮 — 交叉质询】
🔴 激进派反驳保守派：{round2.get('radical_rebuttal', '（缺）')}

🔵 保守派反驳激进派：{round2.get('conservative_rebuttal', '（缺）')}

⚪ 中立派点评：{round2.get('neutral_comment', '（缺）')}

请按以下格式输出最终裁决（用中文）：

## 🏛️ 三方辩论 — 最终裁决

### 辩论摘要
| 派别 | 核心立场 | 最强论据 |
|------|---------|---------|
| 🔴 激进派 | ... | ... |
| 🔵 保守派 | ... | ... |
| ⚪ 中立派 | ... | ... |

### 核心分歧
（双方最根本的分歧点）

### 推荐方案
（有明确倾向的建议，不是各有利弊）

### 关键风险与应对
（如果按推荐方案走，最大的2-3个风险及应对）

### 下一步行动
（24-48小时内可以做的1件具体的事）

### 在什么情况下应该反过来？
（明确写出：如果出现什么信号，应该放弃当前建议、采取相反策略）

⚠️ 不要和稀泥。必须有明确倾向。"""


def main():
    if len(sys.argv) < 2:
        print("用法: python run_debate.py \"你的议题\"", file=sys.stderr)
        print("", file=sys.stderr)
        print("示例: python run_debate.py \"我应该离职创业吗？\"", file=sys.stderr)
        sys.exit(1)
    
    topic = " ".join(sys.argv[1:])
    
    output = {
        "topic": topic,
        "round_1": generate_round1(topic),
        "_usage": {
            "round_1": "用 delegate_task(tasks=output['round_1']) 并行调用 3 个子智能体",
            "round_2": "收集 round_1 结果后，调用 generate_round2(激进派结果, 保守派结果, 中立派结果)，再用 delegate_task(tasks=...) 并行调用",
            "verdict": "收集 round_2 结果后，调用 generate_verdict_prompt(topic, round1_dict, round2_dict)，作为你自己的 prompt 输出最终裁决"
        }
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
