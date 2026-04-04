"""
生成《解密 Claude Code》封面图片
需要: pip install openai
使用: OPENAI_API_KEY=sk-xxx python scripts/generate_cover.py
"""

import os
import sys
from openai import OpenAI

def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("请设置环境变量 OPENAI_API_KEY")
        print("用法: OPENAI_API_KEY=sk-xxx python scripts/generate_cover.py")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    prompt = """
Book cover design for "Demystifying Claude Code" (解密 Claude Code).
Subtitle: "A Source Code Journey of an AI Programming Assistant".

Style: Clean, modern, minimalist tech book cover.
Color scheme: Deep navy blue background with glowing cyan/teal accents.

Central imagery: A stylized terminal window floating in space, with glowing
lines of code streaming out of it, transforming into neural network nodes
and connections. The code lines gradually morph from TypeScript syntax into
abstract light patterns representing AI intelligence.

Around the terminal, show subtle layered architectural diagrams fading into
the background - representing the layered architecture of the software.

A magnifying glass or "decryption" visual element suggesting exploration
and discovery of hidden knowledge.

The overall mood should be: mysterious yet inviting, technical yet
accessible - suitable for a young audience (high school students)
learning about AI software architecture.

No text on the image. Pure illustration only.
Aspect ratio: portrait/vertical book cover format.
"""

    print("正在生成封面图片，请稍候...")

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1792",
        quality="hd",
        n=1,
    )

    image_url = response.data[0].url
    revised_prompt = response.data[0].revised_prompt

    print(f"\n生成成功！")
    print(f"图片 URL: {image_url}")
    print(f"\nDALL-E 修正后的 prompt:\n{revised_prompt}")

    # 下载图片
    import urllib.request
    output_path = os.path.join(os.path.dirname(__file__), "..", "cover.png")
    output_path = os.path.normpath(output_path)

    print(f"\n正在下载到 {output_path} ...")
    urllib.request.urlretrieve(image_url, output_path)
    print("下载完成！封面已保存为 cover.png")


if __name__ == "__main__":
    main()
