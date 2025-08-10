import json
import unittest
from typing import Callable, Any
from uuid import UUID

from mcdreforged import RHoverText, RText, RHoverAction, RColor, RHoverEntity, RHoverEvent, RTextJsonFormat, RHoverItem


class RTextColorTestCase(unittest.TestCase):
	def __test_one(self, hover_event: RHoverEvent, verifier: Callable[[RHoverEvent], Any], json_1_7: dict, json_1_16: dict, json_1_21_5: dict):
		verifier(hover_event)

		self.assertEqual(hover_event.to_json_object(RTextJsonFormat.V_1_7), json_1_7)
		self.assertEqual(hover_event.to_json_object(RTextJsonFormat.V_1_21_5), json_1_21_5)

		verifier(RHoverEvent.from_json_object(json_1_7, RTextJsonFormat.V_1_7))
		verifier(RHoverEvent.from_json_object(json_1_16, RTextJsonFormat.V_1_7))
		verifier(RHoverEvent.from_json_object(json_1_21_5, RTextJsonFormat.V_1_21_5))

	def test_0_hover_text(self):
		def verify(he: RHoverEvent):
			self.assertIsInstance(he, RHoverText)
			self.assertEqual(he.action, RHoverAction.show_text)
			self.assertEqual(he.text, text)

		text = RText('foo', color=RColor.red)
		self.__test_one(
			RHoverText(text=text),
			verifier=verify,
			json_1_7={
				'action': 'show_text',
				'value': {'text': 'foo', 'color': 'red'},
			},
			json_1_16={
				'action': 'show_text',
				'contents': {'text': 'foo', 'color': 'red'},
			},
			json_1_21_5={
				'action': 'show_text',
				'value': {'text': 'foo', 'color': 'red'},
			},
		)

	def test_1_hover_entity(self):
		def verify(he: RHoverEvent):
			self.assertIsInstance(he, RHoverEntity)
			self.assertEqual(he.action, RHoverAction.show_entity)
			self.assertEqual(he.id, 'minecraft:creeper')
			self.assertEqual(str(he.uuid), 'b3e0f8a7-b92a-4289-90cd-af12256aabfa')
			self.assertEqual(he.name, RText('custom name'))

		self.__test_one(
			RHoverEntity(
				id='minecraft:creeper',
				uuid=UUID('b3e0f8a7-b92a-4289-90cd-af12256aabfa'),
				name=RText('custom name'),
			),
			verifier=verify,
			json_1_7={
				'action': 'show_entity',
				'value': json.dumps({
					'type': 'minecraft:creeper',
					'id': 'b3e0f8a7-b92a-4289-90cd-af12256aabfa',
					'name': json.dumps({'text': 'custom name'}, ensure_ascii=False),
				}, ensure_ascii=False),
			},
			json_1_16={
				'action': 'show_entity',
				'contents': {
					'type': 'minecraft:creeper',
					'id': 'b3e0f8a7-b92a-4289-90cd-af12256aabfa',
					'name': {'text': 'custom name'},
				},
			},
			json_1_21_5={
				'action': 'show_entity',
				'id': 'minecraft:creeper',
				'uuid': 'b3e0f8a7-b92a-4289-90cd-af12256aabfa',
				'name': {'text': 'custom name'},
			},
		)

		u = UUID('5ab563fa-4b92-406f-b2c4-2910cf6ee403')
		for uuid_value in [
			str(u),
			str(u).replace('-', ''),
			[u.int >> 96, (u.int >> 64) & 0xFFFFFFFF, (u.int >> 32) & 0xFFFFFFFF, (u.int >> 0) & 0xFFFFFFFF],
		]:
			hover_event = RHoverEvent.from_json_object({
				'action': 'show_entity',
				'id': 'minecraft:creeper',
				'uuid': uuid_value,
			}, RTextJsonFormat.V_1_21_5)
			self.assertIsInstance(hover_event, RHoverEntity)
			self.assertEqual(hover_event.uuid, u)

	def test_2_hover_item(self):
		def verify(he: RHoverEvent):
			self.assertIsInstance(he, RHoverItem)
			self.assertEqual(he.action, RHoverAction.show_item)
			self.assertEqual(he.id, 'minecraft:trident')
			self.assertEqual(he.components, {'Damage': 3})

		self.__test_one(
			RHoverItem(
				id='minecraft:trident',
				count=10,
				components={'Damage': 3},
			),
			verifier=verify,
			json_1_7={
				'action': 'show_item',
				'value': json.dumps({
					'id': 'minecraft:trident',
					'Count': 10,
					'tag': {'Damage': 3},
				}, ensure_ascii=False),
			},
			json_1_16={
				'action': 'show_item',
				'contents': {
					'id': 'minecraft:trident',
					'Count': 10,
					'tag': {'Damage': 3},
				},
			},
			json_1_21_5={
				'action': 'show_item',
				'id': 'minecraft:trident',
				'count': 10,
				# NOTES: actually in mc1.21.5+, this should be {'minecraft:damage': 3} in order to make it work
				# whatever, this is just an unittest
				'components': {'Damage': 3},
			},
		)

	def test_3_rtext_api(self):
		text = RText('foo')

		js_1_7 = {'text': 'foo', 'hoverEvent': {'action': 'show_text', 'value': {'text': 'bar'}}}
		js_1_21_5 = {'text': 'foo', 'hover_event': {'action': 'show_text', 'value': {'text': 'bar'}}}

		text.set_hover_event(RHoverText(text=RText('bar')))
		self.assertEqual(text.to_json_object(json_format=RTextJsonFormat.V_1_7), js_1_7)
		self.assertEqual(text.to_json_object(json_format=RTextJsonFormat.V_1_21_5), js_1_21_5)

		self.assertEqual(text, RText('foo').set_hover_text(RText('bar')))
		self.assertEqual(text, RText('foo').h(RText('bar')))


if __name__ == '__main__':
	unittest.main()
