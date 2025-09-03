# -*- coding: utf-8 -*-
import erniebot, json
from jsonschema import validate


class PromptJson:
	def __init__(self, rulers) -> None:
		self.rulers_str = '请根据下面的schema描述生成给定格式json,只返回json数据,不要其他内容。'
		self.schema_str = ''
		self.example_str = ''

		self.set_rulers(rulers)
		self.set_scheame(self.json_obj())
		self.set_example(self.example())

	def json_obj(self):
		return '''```{'type':'string'}```'''

	def example(self):
		return '正确的示例如下：'

	def __call__(self, *args, **kwargs):
		pass

	def set_scheame(self, json_obj):
		# json转字符串去空格,换行，制表符
		json_str = str(json_obj).replace(' ', '').replace('\n', '').replace('\t', '')
		# 加上三个引号
		json_str = '```' + json_str + '```'
		self.schema_str = json_str

	def set_example(self, example_str:str):
		# 去空格,换行，制表符
		example_str = example_str.replace(' ', '').replace('\n', '').replace('\t', '')
		self.example_str = example_str

	def set_rulers(self, rulers):
		self.rulers_str = rulers.replace(' ', '').replace('\n', '').replace('\t', '')

	def __str__(self) -> str:
		return self.__repr__()

	def __repr__(self) -> str:
		return self.rulers_str + self.schema_str + self.example_str

class FoodPrompt(PromptJson):
    def __init__(self) -> None:
        rulers = '''
你是一个食材识别程序，需要根据输入描述内容，判断对应的食材名称，并返回对应的编号（label），返回格式必须是符合 Schema 的 JSON。

请严格按照如下要求完成任务，并只返回以下格式的 JSON 数据：
1. 根据输入内容识别最可能的食材种类，名称需从下列选项中选择：
   豆腐（1）、西红柿（2）、辣椒（3）、鸡肉（4）、肉（5）、
   芹菜（6）、土豆（7）、花椰菜（8）、绿叶蔬菜（9）、鸡蛋(10)、
   蘑菇（11）、四季豆（12）
2. 返回格式中包含识别出的食材 `name` 和对应的 `label`（数字）；
3. 如果名称存在模糊描述（如“番茄”=“西红柿”、“牛肉”归为“肉”），请根据常识修正；
4. 请根据上下文判断最有可能的食材名称；
5. analysis 字段用于简要说明判断逻辑，限制在20字以内；
6. 只返回JSON数据，不要带有多余解释或自然语言。

输出必须是以下格式：
{
  "name": "食材名称",
  "label": 食材对应的编号,
  "analysis": "简要推理说明（不超过20字）"
}
'''
        super().__init__(rulers)

    def json_obj(self) -> dict:
        schema_food = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "食材名称，必须从给定列表中选择"},
                "label": {"type": "integer", "description": "对应的食材编号"},
                "analysis": {"type": "string", "description": "推理说明，20字以内"}
            },
            "required": ["name", "label", "analysis"]
        }
        return schema_food

    def example(self) -> str:
        example = '''正确的示例如下：
				输入：
				颜色鲜红，汁水丰富，常用于炒鸡蛋，也可生吃，富含番茄红素。

				输出：
				{
				  "name": "西红柿",
				  "label": 2,
				  "analysis": "描述特征符合西红柿"
				}
				输入：
				有一层外层坚硬、中心部分呈黄色或橙色，富含蛋白质，可以水煮、煎、炒、烘培食用。

				输出：
				{
				  "name": "鸡蛋",
				  "label": 10,
				  "analysis": "描述符合鸡蛋特征"
				}
				'''
        return example

class ActionPrompt(PromptJson):
	def __init__(self) -> None:

		rulers = '''你是一个机器人动作规划者，需要把我的话翻译成机器人动作规划并生成对应的json结果，机器人工作空间参考右手坐标系。
					严格按照下面的scheame描述生成给定格式json，只返回json数据:
				'''
		super().__init__(rulers)
		# self.set_rulers(rulers)
		# self.set_scheame(self.json_obj())
		# self.set_example(self.example())

	def json_obj(self)->dict:
		schema_move = {'type': 'object', 'required': ['func', 'x', 'y', 'angle'],
               'porperties':{
                                'func': {'description': '移动', 'const': 'move'},
                                'x': {'description': 'x坐标, 前后移动, 向前移动正值，向后移动负值', 'type': 'number'},
                                'y': {'description': 'y坐标, 左右移动, 向左移动正值，向右移动负值', 'type': 'number'},
                                'angle': {'description': '旋转或者转弯角度，右转顺时针负值，左转逆时针正值', 'type': 'number'}
                            }
            }
		schema_beep = { 'type': 'object', 'required': ['func', 'time_dur'],
				'properties': {'func': {'description': '蜂鸣器,需要发声时', 'const': 'beep'},
                   'time_dur': {'description': '蜂鸣器发声持续时间', 'type': 'number'}}
		}

		schema_light = { 'type': 'object', 'required': ['func', 'time_dur'],
						'properties': {'func': {'description': '发光,需要照明时', 'const': 'light'},
						'time_dur': {'description': '照亮持续时间', 'type': 'number'}}
		}
		schema_actions = {'type': 'array', 'required': ['items'],
                  'items': {'anyOf': [schema_move, schema_beep, schema_light],
                        'minItems': 1
                    }
		}
		return schema_actions

	def example(self)->str:
		example = '''正确的示例如下：
					向左移0.1m, 向左转弯85度: ```[{'func': 'move', 'x': 0, 'y': 0.1, 'angle': 85}]```,
					向右移0.2m, 向前0.1m。 ```[{'func': 'move', 'x': 0.1, 'y': -0.2, 'angle': 0}]```,
					向右转弯85度, 向右移0.1m,。 ```[{'func': 'move', 'x': 0, 'y': -0.1, 'angle': -85}]```,
					蜂鸣器发声5秒。 ```[{'func': 'beep', 'time_dur': 5}]```,
					发光5秒。 ```[{'func': 'light', 'time_dur': 5}]```。
				'''
		return example

class FoodPrompt(PromptJson):
    def __init__(self) -> None:
        rulers = '''
你是一个食材识别程序，需要根据输入描述内容，判断对应的食材名称，并返回对应的编号（label），返回格式必须是符合 Schema 的 JSON。

请严格按照如下要求完成任务，并只返回以下格式的 JSON 数据：
1. 根据输入内容识别最可能的食材种类，名称需从下列选项中选择：
   豆腐（1）、西红柿（2）、辣椒（3）、鸡肉（4）、肉（5）、
   芹菜（6）、土豆（7）、花椰菜（8）、绿叶蔬菜（9）、鸡蛋(10)、
   蘑菇（11）、四季豆（12）

2. 返回格式中包含识别出的食材 `name` 和对应的 `label`（数字）；
3. 如果名称存在模糊描述（如“番茄”=“西红柿”、“牛肉”归为“肉”），请根据常识修正；
4. 请根据上下文判断最有可能的食材名称；
5. analysis 字段用于简要说明判断逻辑，限制在20字以内；
6. 只返回JSON数据，不要带有多余解释或自然语言。

输出必须是以下格式：
{
  "name": "食材名称",
  "label": 食材对应的编号,
  "analysis": "简要推理说明（不超过20字）"
}
'''
        super().__init__(rulers)

    def json_obj(self) -> dict:
        schema_food = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "食材名称，必须从给定列表中选择"},
                "label": {"type": "integer", "description": "对应的食材编号"},
                "analysis": {"type": "string", "description": "推理说明，20字以内"}
            },
            "required": ["name", "label", "analysis"]
        }
        return schema_food

    def example(self) -> str:
        example = '''正确的示例如下：
			输入：
			颜色鲜红，汁水丰富，常用于炒鸡蛋，也可生吃，富含番茄红素。

			输出：
			{
			  "name": "西红柿",
			  "label": 2,
			  "analysis": "描述特征符合西红柿"
			}

			输入：
			有一层外层坚硬、中心部分呈黄色或橙色，富含蛋白质，可以水煮、煎、炒、烘培食用。

			输出：
			{
			  "name": "鸡蛋",
			  "label": 10,
			  "analysis": "描述符合鸡蛋特征"
			'''
        return example


class IngredientsAnswerAnalysisPrompt(PromptJson):
    def __init__(self) -> None:
        rulers = '''
你是一个专业的“菜肴食材匹配分析器”，任务是从4条描述中选出**最符合给定食材特征**的一条。请严格遵循以下规则：

### 核心规则
1. **禁止捏造事实**：仅基于描述内容判断，不可添加描述中未出现的信息（如示例中的错误：描述未提“红黄”却分析“红黄酱汁”）。
2. **匹配依据**（优先级从高到低）：
   - 是否明确提及食材关键词（如“鸡蛋”“肉”）；
   - 风味是否符合食材组合的常见特征（如“酸甜”对番茄鸡蛋，“辛辣”对辣椒炒肉）；
   - 烹饪特征是否吻合（如“软烂出汁”对西红柿，“外酥里嫩”对炸物）。
3. **必须选择最接近项**：即使所有描述不完美，也需选出相对最佳的一条，**不可返回-1**。
4. **禁用语言风格判断**：仅关注食材与风味匹配度，忽略修辞手法。
5. **直接特征优先**：若描述同时存在直接特征（如颜色、质地）与间接特性（如“酸甜”），优先选择直接特征匹配项（参考规则6示例）。

### 输入输出格式
- 输入格式：
  描述：
  0: [文本]
  1: [文本]
  2: [文本]
  3: [文本]
  已获取的食材为：[食材1]、[食材2]
- 输出格式（JSON）：
  {
    "row": 最匹配的编号（0~3）,
    "analysis": "25字内原因，需引用描述关键词（如：提及‘红黄相间’）"
  }

### 案例示范
▼ 示例1（正确执行）：
输入：
描述：
0: 表面油亮，呈鲜亮绿色，口感清脆
1: 红黄相间，软烂出汁
2: 酱汁深褐酸甜，外酥里嫩
3: 深绿辣椒与肉混合，辛辣焦香
食材：辣椒、肉
输出：
{"row": 3, "analysis": "提及辣椒与肉，辛辣焦香匹配"}

▼ 示例2（错误规避）：
输入：
描述：
0: 清淡爽口，蔬菜清香
1: 红黄相间，软烂出汁
2: 酱汁深褐酸甜，外酥里嫩
3: 深绿切片与肉混合，辛辣咸香
食材：西红柿、鸡蛋
错误输出（分析捏造事实）：{"row": 2, "analysis": "酸甜符合番茄鸡蛋"}
正确输出：{"row": 1, "analysis": "红黄相间符合番茄鸡蛋颜色"}
        '''
        super().__init__(rulers)

    def json_obj(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "row": {"type": "integer", "description": "最匹配的描述编号（0~3）"},
                "analysis": {"type": "string", "description": "25字内原因，需引用描述关键词"}
            },
            "required": ["row", "analysis"]
        }

    def example(self) -> str:
        return '''示例输入：
描述：
0: 清淡爽口，蔬菜清香
1: 酸甜口感，红黄酱汁
2: 酱汁浓郁，外酥里嫩
3: 深绿辣椒与肉混合，辛辣焦香
食材：辣椒、肉
输出：
{"row": 3, "analysis": "提及辣椒肉，辛辣焦香匹配"}
'''


class TaskAnswerPrompt(PromptJson):
	def __init__(self) -> None:
		rulers = '''
		你是一个答题程序，需要根据OCR识别的文本内容，判断题目及选项，并推理出最合理的正确答案。OCR文本包含题目及4个选项，格式可能含错别字、漏字、断句错误等问题，你的任务包括以下内容：

		【你的任务要求】
		1. **OCR结果可能包含错别字和语病**，请根据上下文和常识自动纠错（如“香焦”应为“香蕉”，“终支付”应为“最终支付”）。
		2. **识别并拆分题干与选项**，并推理出最合理选项。注意选项为题干后的连续4项，形式如 `0:内容 1:内容 2:内容 3:内容`。
		3. 必须进行**数学或语义推理**，尤其在题目涉及计算时（如优惠、价格等），需根据文本信息列算式并判断。
		4. 题目可能不完整或含模糊描述，**不能凭空捏造内容**，应从上下文中合理推测答案。
		5. **答案格式仅限如下JSON结构**，请勿输出任何其他文字、解释、markdown符号或引号等：

		{
		"answer": 选项编号（整数0-3）,
		"analysis": "不超过20字的推理说明"
		}

		【示例1】
		输入：
		如果买满200元可优惠30元。购买了3件商品，价格分别为85元、130元和115元。最终支付多少钱? 0:180元 1:300元 2:210元 3:330元

		输出：
		{
		"answer": 1,
		"analysis": "总价330减30得300"
		}

		【示例2】
		输入：
		买满300元可优惠50元，购买了3件商品，价格分别为120元，130元，100元，最终支付多少钱? 0:140元 1:310元 2:290元 3:300元

		输出：
		{
		"answer": 3,
		"analysis": "总价350减50得300"
		}

		【注意】
		- 若题干中存在错字（如“终支付”应为“最终支付”），请**自动修正后再判断**。
		- 必须返回答案编号（从左到右的编号），**不得返回具体内容文本**。
		- **永远只输出标准JSON结构，不允许包含注释、反引号、markdown格式或多余说明。**

		'''

		super().__init__(rulers)

	def json_obj(self) -> dict:
		schema_task_answer = {
			"type": "object",
			"properties": {
				"answer": {"type": "integer", "description": "从左往右匹配的正确答案选项编号"},
				"analysis": {"type": "string", "description": "题目分析过程，限制20字以内"}
			},
			"required": ["answer", "analysis"]
		}
		return schema_task_answer

	def example(self) -> str:
		example = '''正确的示例如下：
		输入：
		如果买满200元可优惠30元。购买了3件商品，价格分别为85元、130元和115元。最终支付多少钱 0:180元 1:300元 2:210元 3:330元

		输出：
		{
		  "answer": 1,
		  "analysis": "总价330减30得300"
		}

		输入：
		买满300元可优惠50元，购买了3件商品，价格分别为120元，130元，100元，最终支付多少钱? 0: 140元 1: 310元 2: 290元 3: 300元
		输出：
		{
		  "answer": 3,
		  "analysis": ”总价为350元，优惠50元，350-50=300元“
		}

		'''
		return example

class HumAttrPrompt(PromptJson):
	def __init__(self) -> None:
		rulers = '''你是一个人特征总结程序，需要根据描述把人的特征生成对应的json结果，如果有对应的描述就写入对应位置。
					严格按照下面的scheame描述生成给定格式json，只返回json数据:
				'''
		super().__init__(rulers)

	def json_obj(self)->dict:
		'''
		0 = Hat - 帽子:0无1有
		1 = Glasses - 眼镜:0无1有
		2 = ShortSleeve - 短袖
		3 = LongSleeve - 长袖
		4 = UpperStride - 有条纹
		5 = UpperLogo - 印有logo/图案
		6 = UpperPlaid - 撞色衣服(多种颜色)
		7 = UpperSplice - 格子衫
		8 = LowerStripe - 有条纹
		9 = LowerPattern - 印有图像
		10 = LongCoat - 长款大衣
		11 = Trousers - 长裤
		12 = Shorts - 短裤
		13 = Skirt&Dress - 裙子/连衣裙
		14 = boots - 鞋子
		15 = HandBag - 手提包
		16 = ShoulderBag - 单肩包
		17 = Backpack - 背包
		18 = HoldObjectsInFront - 手持物品
		19 = AgeOver60 - 大于60
		20 = Age18-60 - =18~60
		21 = AgeLess18 - 小于18
		22 = Female - 0:男性; 1:女性
		23 = Front - 人体朝前
		24 = Side - 人体朝侧
		25 = Back - 人体朝后
		'''
		schema_attr = {'type': 'object',
                'properties':{
                    'hat':{'type': 'boolean', 'description': '戴帽子真,没戴帽子假'},
					'glasses': {"type": 'boolean', 'description': '戴眼镜真,没戴眼镜假', 'threshold':0.15},
					'sleeve':{'enum': ['Short', 'Long'], 'description': '衣袖长短'},
					# 'UpperStride', 'UpperLogo', 'UpperPlaid', 'UpperSplice'	有条纹		印有logo/图案	撞色衣服(多种颜色) 格子衫
					'color_upper':{'enum':['Stride', 'Logo', 'Plaid', 'Splice'], 'description': '上衣衣服颜色'},
					# 'LowerStripe', 'LowerPattern'		有条纹		印有图像
					'color_lower':{'enum':['Stripe', 'Pattern'], 'description': '下衣衣服长短'},
					# 'LongCoat', 长款大衣
					'clothes_upper':{'enum':['LongCoat'], 'description': '上衣衣服类型', 'threshold':0.8},
					# 'Trousers', 'Shorts', 'Skirt&Dress'  长裤		短裤 	裙子/连衣裙
					'clothes_lower':{'enum':['Trousers', 'Shorts', 'Skirt_dress'], 'description': '下衣衣服类型'},
					'boots':{'type': 'boolean', 'description': '穿着鞋子真,没穿鞋子假'},
					'bag':{'enum': ['HandBag', 'ShoulderBag', 'Backpack'], 'description': '带着包的类型'},
					'holding':{'type': 'boolean', 'description': '持有物品为真', 'threshold':0.5},
					'age':{'enum': ['Old', 'Middle', 'Young'], 'description': '年龄,小于18岁为young, 18到60为middle, 大于60为old'},
					'sex':{'enum': ['Female', 'Male'], 'threshold':0.6},
					'direction':{'enum': ['Front', 'Side', 'Back'], 'description': '人体朝向'},
					},
                "additionalProperties": False
            }
		return schema_attr

	def example(self)->str:
		example = '''正确的示例如下：
					一个带着眼镜的老人: ```{'glasses': True, 'age': 'old'}```,
					一个带着帽子的中年人: ```{'hat': True, 'age': 'middle'}``` ,
					穿着短袖的带着眼镜的人: ```{'glasses': True, 'clothes': 'short'}``` 。
				'''
		return example

class EduCounselerPrompt(PromptJson):
	def __init__(self) -> None:
		rulers = '''你是一个人中小学指导程序，需要根据描述的题目，逐步进行推理，根据给出的选项选择出正确答案的json结果。
					严格按照下面的scheame描述生成给定格式json，只返回json数据:
				'''
		super().__init__(rulers)

	def json_obj(self)->dict:
		schema_edu = {
						"type": "object", "required": ['answer', 'analysis'],
						"properties": {
							"analysis":{'type':"string", "description":"题目分析的具体过程,分析的过程少于20字"},
							"answer": {'enum': ['A', 'B', 'C', "D"], "description": "答案选项中的一个"}
						},
						"additionalProperties": False
            		 }
		return schema_edu

	def example(self)->str:
		example = '''正确的示例如下：
					题目: 1+1=？, 答案选项有: A.4 B.44 C.7 D.2 ```{"description":"1+1的结果是2,其中选项D和答案一致,所以选D",'answer': 'D'}``` ,
					题目: 1+2=？, 答案选项有: A.3 B.44 C.6 D.2: ```{"description":"1+2的结果是3,其中选项A和答案一致,所以选A",'answer': 'A'}``` 。'''
		return example

class ErnieBotWrap():

	def __init__(self):
		erniebot.api_type = 'aistudio'
		erniebot.access_token = 'fe7ef5f4bec866a3c3d48b0f7717740bd6506144'
		models = erniebot.Model.list()
		print(models)

		self.msgs = []
		self.model = 'ernie-4.0'
		# self.model = 'ernie-3.5'
		# self.model = 'ernie-turbo'
		# self.model = "ernie-text-embedding"
		# self.model = "ernie-vilg-v2"
		self.prompt_str = '请根据下面的描述生成给定格式json'

	@staticmethod
	def get_mes(role, dilog):
		data = {}
		if role == 0:
			data['role'] = 'user'
		elif role ==1:
			data['role'] = 'assistant'
		data['content'] = dilog
		return data

	def set_promt(self, prompt_str):
		# str_input = prompt_str
		# self.msgs.append(self.get_mes(0, str_input))
		# response = erniebot.ChatCompletion.create(model=self.model, messages=self.msgs, system=prompt_str)
		# str_res = response.get_result()
		# self.msgs.append(self.get_mes(1, str_res))
		# print(str_res)
		# print("设置成功")
		self.prompt_str = prompt_str
		# print(self.prompt_str)


	def get_res(self, str_input, record=False, request_timeout=5):
		print(len(str_input), str_input)
		if len(str_input)<1:
			return False, None
		start_str = " ```"
		end_str = " ```, 根据这段描述生成给定格式json"
		str_input = start_str + str_input + end_str
		msg_tmp = self.get_mes(0, str_input)
		if record:
			self.msgs.append(msg_tmp)
			msgs = self.msgs
		else:
			msgs = [msg_tmp]
		# Create a chat completion
		try:
			response = erniebot.ChatCompletion.create(model=self.model, messages=msgs, system=self.prompt_str, top_p=0.1,
											_config_=dict(api_type="AISTUDIO",), request_timeout=request_timeout)
		except Exception as e:
			print(e)
			return False, None
		# _config_=dict(api_type="QIANFAN",)
		# _config_=dict(api_type="AISTUDIO",)
		print(response)
		str_res = response.get_result()
		if record:
			self.msgs.append(self.get_mes(1, str_res))
		return True, str_res

	@staticmethod
	def get_json_str(json_str:str):
		try:
			index_s = json_str.find("```json")
			if index_s == -1:
				index_s = json_str.find("```")
				if index_s == -1:
					return None
				else:
					index_s += 3

			else:
				index_s += 7
			# print(json_str[index_s:])
			index_e = json_str[index_s:].find("```") + index_s
			if index_e == -1:
				return None
			# json_str = json_str[index_s:index_e]
			# print(json_str[index_s:index_e])
			# print(index_s, index_e)
			json_str = json_str[index_s:index_e]
			# 找到注释内容并删除
			json_str.replace("\n", "")
			# print(json_str)
			msg_json = json.loads(json_str)
			return msg_json
			# print(index_s)
			# return json_str
		except Exception as e:
			# print(e)
			return json_str
			'''
			try:
				index_s = json_str.find("```json") + 7
				# index_s = json_str.find("```json") + 7
			except Exception as e:
				index_s = 0
			try:
				index_e = json_str[index_s:].find("```") + index_s
			except Exception as e:
				index_e = len(json_str)
			import json
			msg_json = json.loads(json_str[index_s:index_e])
			return msg_json
			'''

	def get_res_json(self, str_input, record=False, request_timeout=10):
		state, str_res = self.get_res(str_input, record, request_timeout)
		#print("state:",state,"str_res", str_res)
		if state:
			# print(str_res)
			obj_json = self.get_json_str(str_res)
			return obj_json
		else:
			return None

def test():
	res = '''```json\n[\n  {\n    "func": "my_light",\n    "count": 3\n  },\n  {\n    "func": "beep",\n    "time_dur": 3  // 假设蜂鸣器持续发声3秒作为紧急警示，具体时长可根据实际情况调整\n  }\n]\n```'''
	json_test = ErnieBotWrap.get_json_str(res)
	print(json_test)



if __name__ == "__main__":
	# test()
	str_input = ''' 如果买满200元可优惠40元。购买了3件商品,价格分别为85元、130元和115元。最终支付多少钱?	选项有: A.300元 B.180元 C.130元 D.290元'''

	# ernie_edu = EduCounselerPrompt()

	ernie = ErnieBotWrap()
	# 设置prompt
	# ernie.set_promt(str(ActionPrompt()))
	# ernie.set_promt(str(HumAttrPrompt()))
	ernie.set_promt(str(EduCounselerPrompt()))
	json_res = ernie.get_res_json(str_input)
	print(json_res)
	# while True:
	# 	print("用户")
	# 	str_tmp = input("输入:")
	# 	if len(str_tmp)<1:
	# 		continue
	# 	# Create a chat completion
	# 	print("文心一言")
	# 	# _, str_res = ernie.get_res(str_tmp)
	# 	json_res = ernie.get_res_json(str_tmp)
	# 	print("输出:",json_res)

