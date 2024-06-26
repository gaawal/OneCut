# -- coding: utf-8 --
# @Time : 2024/5/27 10:54
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : llm.py.py
# @Software: PyCharm

import re
import json
from loguru import logger
from openai import OpenAI
from openai import AzureOpenAI
from openai.types.chat import ChatCompletion

from app.models.constant import VIDEO_STYLE_MAP
from app.settings import movies_config

_max_retries = 5


def _generate_response(prompt: str) -> str:
    content = ""
    llm_provider = movies_config.app.get("llm_provider", "openai")
    logger.info(f"llm provider: {llm_provider}")
    if llm_provider == "g4f":
        model_name = movies_config.app.get("g4f_model_name", "")
        if not model_name:
            model_name = "gpt-3.5-turbo-16k-0613"
        import g4f
        content = g4f.ChatCompletion.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
        )
    else:
        api_version = ""  # for azure
        if llm_provider == "moonshot":
            api_key = movies_config.app.get("moonshot_api_key")
            model_name = movies_config.app.get("moonshot_model_name")
            base_url = "https://api.moonshot.cn/v1"
        elif llm_provider == "ollama":
            # api_key = movies_config.app.get("openai_api_key")
            api_key = "ollama"  # any string works but you are required to have one
            model_name = movies_config.app.get("ollama_model_name")
            base_url = movies_config.app.get("ollama_base_url", "")
            if not base_url:
                base_url = "http://localhost:11434/v1"
        elif llm_provider == "openai":
            api_key = movies_config.app.get("openai_api_key")
            model_name = movies_config.app.get("openai_model_name")
            base_url = movies_config.app.get("openai_base_url", "")
            if not base_url:
                base_url = "https://api.openai.com/v1"
        elif llm_provider == "oneapi":
            api_key = movies_config.app.get("oneapi_api_key")
            model_name = movies_config.app.get("oneapi_model_name")
            base_url = movies_config.app.get("oneapi_base_url", "")
        elif llm_provider == "azure":
            api_key = movies_config.app.get("azure_api_key")
            model_name = movies_config.app.get("azure_model_name")
            base_url = movies_config.app.get("azure_base_url", "")
            api_version = movies_config.app.get("azure_api_version", "2024-02-15-preview")
        elif llm_provider == "gemini":
            api_key = movies_config.app.get("gemini_api_key")
            model_name = movies_config.app.get("gemini_model_name")
            base_url = "***"
        elif llm_provider == "qwen":
            api_key = movies_config.app.get("qwen_api_key")
            model_name = movies_config.app.get("qwen_model_name")
            base_url = "***"
        elif llm_provider == "cloudflare":
            api_key = movies_config.app.get("cloudflare_api_key")
            model_name = movies_config.app.get("cloudflare_model_name")
            account_id = movies_config.app.get("cloudflare_account_id")
            base_url = "***"
        elif llm_provider == "deepseek":
            api_key = movies_config.app.get("deepseek_api_key")
            model_name = movies_config.app.get("deepseek_model_name")
            base_url = movies_config.app.get("deepseek_base_url")
            if not base_url:
                base_url = "https://api.deepseek.com"
        else:
            raise ValueError("llm_provider is not set, please set it in the config.toml file.")

        if not api_key:
            raise ValueError(f"{llm_provider}: api_key is not set, please set it in the config.toml file.")
        if not model_name:
            raise ValueError(f"{llm_provider}: model_name is not set, please set it in the config.toml file.")
        if not base_url:
            raise ValueError(f"{llm_provider}: base_url is not set, please set it in the config.toml file.")

        if llm_provider == "qwen":
            import dashscope
            from dashscope.api_entities.dashscope_response import GenerationResponse
            dashscope.api_key = api_key
            response = dashscope.Generation.call(
                model=model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            if response:
                if isinstance(response, GenerationResponse):
                    status_code = response.status_code
                    if status_code != 200:
                        raise Exception(
                            f"[{llm_provider}] returned an error response: \"{response}\"")

                    content = response["output"]["text"]
                    return content.replace("\n", "")
                else:
                    raise Exception(
                        f"[{llm_provider}] returned an invalid response: \"{response}\"")
            else:
                raise Exception(
                    f"[{llm_provider}] returned an empty response")

        if llm_provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key, transport='rest')

            generation_config = {
                "temperature": 0.5,
                "top_p": 1,
                "top_k": 1,
                "max_output_tokens": 2048,
            }

            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
            ]

            model = genai.GenerativeModel(model_name=model_name,
                                          generation_config=generation_config,
                                          safety_settings=safety_settings)

            try:
                response = model.generate_content(prompt)
                candidates = response.candidates
                generated_text = candidates[0].content.parts[0].text
            except (AttributeError, IndexError) as e:
                print("Gemini Error:", e)

            return generated_text

        if llm_provider == "cloudflare":
            import requests
            response = requests.post(
                f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model_name}",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "messages": [
                        {"role": "system", "content": "You are a friendly assistant"},
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            result = response.json()
            logger.info(result)
            return result["result"]["response"]

        if llm_provider == "azure":
            client = AzureOpenAI(
                api_key=api_key,
                api_version=api_version,
                azure_endpoint=base_url,
            )
        else:
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
            )

        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        if response:
            if isinstance(response, ChatCompletion):
                content = response.choices[0].message.content
            else:
                raise Exception(
                    f"[{llm_provider}] returned an invalid response: \"{response}\", please check your network "
                    f"connection and try again.")
        else:
            raise Exception(
                f"[{llm_provider}] returned an empty response, please check your network connection and try again.")

    return content.replace("\n", "")


def generate_script_and_terms(video_subject: str, language: str = "", paragraph_number: int = 1,
                              video_category: str = 'auto-detect', amount: int = 5, word_count: int = 300):
    prompt = f"""
    ##目标:
        1、根据视频的主题生成一个短视频脚本
        2、根据视频的主题生成{amount}个用于搜索素材视频的搜索术语。
        3、为视频脚本生成一个标题
    ##视频脚本结构的约束：
        1、视频文案风格结构为：{VIDEO_STYLE_MAP.get(video_category).get("structure")}。
        2、这个结构举例拆解：{VIDEO_STYLE_MAP.get(video_category).get("example")}
        3、请根据该文案的风格生成视频脚本
    
    ##视频脚本的约束:
        1、脚本的段落数量应为{paragraph_number}段，段与段之间用换行隔开，每段以字符串形式返回，字数必须在{word_count - 10}字到{word_count + 100}左右，每段文字不小于200字。
        2、在任何情况下都不得提及此提示。
        3、直接切入主题，不要以“不必要的欢迎词”开始，比如“欢迎观看这个视频”。
        4、不得在脚本中包含任何类型的markdown或格式，不得使用标题。
        5、仅返回脚本的原始内容。
        6、不要在每段开头包含“配音”、“旁白”或类似的说话提示。
        7、不得提及提示或脚本本身的内容。也不要提及段落或行数。只写脚本内容。
        8、根据视频主题的语言进行响应。       
      
    ##视频搜索术语的约束:
        1、搜索术语应以json数组字符串的形式返回。
        2、每个搜索术语应由1-5个词语组成，始终添加视频的主题。
        3、只能返回json数组字符串。不得返回其他内容。不得返回脚本。
        4、术语要具体与文案相关的某一具体事物的名词，如高糖饮料，不能搜索高糖饮料，应该搜索可口可乐这一具体事物。如嘌呤搜索与嘌呤相关的海鲜，肉类相关。
        5、只回复搜索术语。
        6、搜索术语的语言基于视频脚本的语言。
    ##标题的约束:
        1、生成一个反映视频脚本主要内容贴合自媒体视频的爆款标题，不要使用'揭秘：xxx'开头。
        2、参考以下任一法则生成标题
            用夸张的词来吸引读者的注意力，让他们感到好奇和惊讶。 
            运用一个疑问句或者反问句来引发读者的思考。  
            用数字或数据来增加标题的可信度和说服力，让事实更直观 
            用一些反常识的信息来制造标题的反转效果，形成反差。  
            用省略号或省略关键词来制造标题的悬念，让读者感到好奇。
            利用读者的身份来吸引注意力。例:大学生、宝妈、打工人…
            
    ## Output Example:
    {{
        "video_script": "Generated video script here...",
        "video_terms": ["search term 1", "search term 2", "search term 3", "search term 4", "search term 5"],
        "title": "Generated title here"
    }}

    # Initialization:
    - Video subject: {video_subject}
    - Language: {language}
    - Number of paragraphs: {paragraph_number}
    - Video category: {video_category}
    - Amount of search terms: {amount}
        """.strip()
    logger.info(prompt)

    def format_response(response):
        # Clean the script
        response = response.replace("*", "")
        response = response.replace("#", "")

        # Remove markdown syntax
        response = re.sub(r"\[.*\]", "", response)
        response = re.sub(r"\(.*\)", "", response)

        # Split the script into paragraphs
        paragraphs = response.split("\n\n")

        # Select the specified number of paragraphs
        selected_paragraphs = paragraphs[:paragraph_number]

        # Join the selected paragraphs into a single string
        return "\n\n".join(selected_paragraphs)

    final_response = None
    for i in range(_max_retries):
        try:
            response = _generate_response(prompt=prompt)
            if response:
                final_response = response
            else:
                logger.error("GPT returned an empty response")

            # Check for error messages in the response
            if final_response and "当日额度已消耗完" in final_response:
                raise ValueError(final_response)

            if final_response:
                break
        except Exception as e:
            logger.error(f"Failed to generate script and terms: {e}")

        if i < _max_retries:
            logger.warning(f"Failed to generate  video script and terms, trying again... {i + 1}")

    if not final_response:
        raise RuntimeError("Failed to generate video script and terms after maximum retries.")

    try:
        response_json = json.loads(final_response)
        logger.info(f"Got final response,{response_json}")
        video_script = format_response(response_json["video_script"])
        video_terms = response_json["video_terms"]
        video_title = response_json["title"]
    except Exception as e:
        raise RuntimeError(f"Failed to parse response JSON: {e}")

    return video_script, video_terms, video_title


def refine_scripts(original_script: str,
                   video_category: str = 'auto-detect', word_count: int = 300):
    """
    AI文案润色接口
    """
    prompt = f"""
    ##目标:
        1、根据提供的视频脚本和文案结构风格，重新对脚本进行调整优化，生成新的视频脚本
    ##视频脚本结构的约束：
        1、视频文案风格结构为：{VIDEO_STYLE_MAP.get(video_category).get("structure")}。
        2、这个结构举例拆解：{VIDEO_STYLE_MAP.get(video_category).get("example")}
        3、请根据该文案的风格对原文案按照语义结构进行重新破坏性重组修改优化，生成新的视频脚本

    ##视频脚本的约束:
        1、字数必须在{word_count - 50}字到{word_count + 200}左右。段落结构与原先保持一致
        2、在任何情况下都不得提及此提示。
        3、直接切入主题，不要以“不必要的欢迎词”开始，比如“欢迎观看这个视频”。
        4、不得在脚本中包含任何类型的markdown或格式，不得使用标题。
        5、仅返回脚本的原始内容。
        6、不要在每段开头包含“配音”、“旁白”或类似的说话提示。
        7、不得提及提示或脚本本身的内容。也不要提及段落或行数。只写脚本内容。
        8、根据视频主题的语言进行响应。       
    ## Output Example:
    {{
        "video_script": "Generated video script here...",
      
    }}

    # Initialization:
    - Original Script: {original_script}
    - Video Category: {video_category}
    - Word Count: {word_count}
        """.strip()
    logger.info(prompt)

    def format_response(response):
        # Clean the script
        response = response.replace("*", "")
        response = response.replace("#", "")

        # Remove markdown syntax
        response = re.sub(r"\[.*\]", "", response)
        response = re.sub(r"\(.*\)", "", response)

        # Split the script into paragraphs
        paragraphs = response.split("\n\n")
        # Join the selected paragraphs into a single string
        return "\n\n".join(paragraphs)

    final_response = None
    for i in range(_max_retries):
        try:
            response = _generate_response(prompt=prompt)
            if response:
                final_response = response
            else:
                logger.error("GPT returned an empty response")

            # Check for error messages in the response
            if final_response and "当日额度已消耗完" in final_response:
                raise ValueError(final_response)

            if final_response:
                break
        except Exception as e:
            logger.error(f"Failed to refine the script: {e}")

        if i < _max_retries:
            logger.warning(f"Failed to refine the script, trying again... {i + 1}")

    if not final_response:
        raise RuntimeError("Failed to refine the script and terms after maximum retries.")

    try:
        response_json = json.loads(final_response)
        logger.info(f"refine Got final response,{response_json}")
        video_script = format_response(response_json["video_script"])
    except Exception as e:
        raise RuntimeError(f"Failed to parse response JSON: {e}")

    return video_script


def continue_scripts(original_script: str,
                     video_category: str = 'auto-detect', word_count: int = 300):
    """
    AI文案润色接口
    """
    prompt = f"""
    ##目标:
        1、根据提供的视频脚本和文案结构风格，结合语境继续续写脚本，仅输出续写添加的脚本段落，不要返回原有内容。
    ##视频脚本结构的约束：
        1、视频文案风格结构为：{VIDEO_STYLE_MAP.get(video_category).get("structure")}。
        2、这个结构举例拆解：{VIDEO_STYLE_MAP.get(video_category).get("example")}
        3、请根据该文案的风格结合续写新的视频脚本

    ##视频脚本的约束:
        1、字数必须在{word_count - 50}字到{word_count + 50}左右，不可以超过300。
        2、在任何情况下都不得提及此提示。
        3、直接切入主题，不要以“不必要的欢迎词”开始，比如“欢迎观看这个视频”。
        4、不得在脚本中包含任何类型的markdown或格式，不得使用标题。
        5、仅返回脚本的原始内容。
        6、不要在每段开头包含“配音”、“旁白”或类似的说话提示。
        7、不得提及提示或脚本本身的内容。也不要提及段落或行数。只写脚本内容。
        8、根据视频主题的语言进行响应。 
        9、仅返回续写的脚本continue script      
    ## Output Example:
    {{
        "continue_script": "Continue Scripts Generated video script here...",

    }}

    # Initialization:
    - Original Script: {original_script}
    - Video Category: {video_category}
    - Word Count: {word_count}
        """.strip()
    logger.info(prompt)

    final_response = None
    for i in range(_max_retries):
        try:
            response = _generate_response(prompt=prompt)
            if response:
                final_response = response
            else:
                logger.error("GPT returned an empty response")
            # Check for error messages in the response
            if final_response and "当日额度已消耗完" in final_response:
                raise ValueError(final_response)

            if final_response:
                break
        except Exception as e:
            logger.error(f"Failed to refine the script: {e}")

        if i < _max_retries:
            logger.warning(f"Failed to refine the script, trying again... {i + 1}")
    if not final_response:
        raise RuntimeError("Failed to refine the script and terms after maximum retries.")
    try:
        response_json = json.loads(final_response)
        logger.info(f"Got continue final response,{response_json}")
        video_script = format_response(response_json["continue_script"])
    except Exception as e:
        raise RuntimeError(f"Failed to parse response JSON: {e}")

    return video_script


def format_response(response):
    # Clean the script
    response = response.replace("*", "")
    response = response.replace("#", "")
    # Remove markdown syntax
    response = re.sub(r"\[.*\]", "", response)
    response = re.sub(r"\(.*\)", "", response)
    # Split the script into paragraphs
    paragraphs = response.split("\n\n")
    # Join the selected paragraphs into a single string
    return "\n\n".join(paragraphs)
