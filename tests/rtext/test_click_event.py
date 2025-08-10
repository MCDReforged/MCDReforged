import unittest
from typing import Callable, Any, Optional

from mcdreforged import RText, RClickAction, RClickSuggestCommand, RTextJsonFormat, RClickEvent, RClickRunCommand, RClickOpenUrl, RClickCopyToClipboard, RClickOpenFile
from mcdreforged.minecraft.rtext.click_event import RClickChangePage, RClickShowDialog, RClickCustom


class RTextColorTestCase(unittest.TestCase):
	def __test_one(self, click_event: RClickEvent, verifier: Callable[[RClickEvent], Any], json_1_7: Optional[dict], json_1_21_5: dict):
		verifier(click_event)

		if json_1_7 is not None:
			self.assertEqual(click_event.to_json_object(RTextJsonFormat.V_1_7), json_1_7)
		else:
			click_event.to_json_object(RTextJsonFormat.V_1_7)  # just don't crash
		self.assertEqual(click_event.to_json_object(RTextJsonFormat.V_1_21_5), json_1_21_5)

		if json_1_7 is not None:
			verifier(RClickEvent.from_json_object(json_1_7, RTextJsonFormat.V_1_7))
		verifier(RClickEvent.from_json_object(json_1_21_5, RTextJsonFormat.V_1_21_5))

	def test_0_suggest_command(self):
		def verify(ce: RClickEvent):
			self.assertIsInstance(ce, RClickSuggestCommand)
			self.assertEqual(ce.action, RClickAction.suggest_command)
			self.assertEqual(ce.command, '/say foo')

		self.__test_one(
			RClickSuggestCommand('/say foo'),
			verifier=verify,
			json_1_7={'action': 'suggest_command', 'value': '/say foo'},
			json_1_21_5={'action': 'suggest_command', 'command': '/say foo'},
		)

	def test_1_run_command(self):
		def verify(ce: RClickEvent):
			self.assertIsInstance(ce, RClickRunCommand)
			self.assertEqual(ce.action, RClickAction.run_command)
			self.assertEqual(ce.command, '/say bar')

		self.__test_one(
			RClickRunCommand('/say bar'),
			verifier=verify,
			json_1_7={'action': 'run_command', 'value': '/say bar'},
			json_1_21_5={'action': 'run_command', 'command': '/say bar'},
		)

	def test_2_open_url(self):
		def verify(ce: RClickEvent):
			self.assertIsInstance(ce, RClickOpenUrl)
			self.assertEqual(ce.action, RClickAction.open_url)
			self.assertEqual(ce.url, 'https://github.com')

		self.__test_one(
			RClickOpenUrl('https://github.com'),
			verifier=verify,
			json_1_7={'action': 'open_url', 'value': 'https://github.com'},
			json_1_21_5={'action': 'open_url', 'url': 'https://github.com'},
		)

	def test_3_open_url(self):
		def verify(ce: RClickEvent):
			self.assertIsInstance(ce, RClickOpenFile)
			self.assertEqual(ce.action, RClickAction.open_file)
			self.assertEqual(ce.path, '/foo/bar')

		self.__test_one(
			RClickOpenFile('/foo/bar'),
			verifier=verify,
			json_1_7={'action': 'open_file', 'value': '/foo/bar'},
			json_1_21_5={'action': 'open_file', 'path': '/foo/bar'},
		)

	def test_4_copy_to_clipboard(self):
		def verify(ce: RClickEvent):
			self.assertIsInstance(ce, RClickCopyToClipboard)
			self.assertEqual(ce.action, RClickAction.copy_to_clipboard)
			self.assertEqual(ce.value, 'foo bar')

		self.__test_one(
			RClickCopyToClipboard('foo bar'),
			verifier=verify,
			json_1_7={'action': 'copy_to_clipboard', 'value': 'foo bar'},
			json_1_21_5={'action': 'copy_to_clipboard', 'value': 'foo bar'},
		)

	def test_5_change_page(self):
		def verify(ce: RClickEvent):
			self.assertIsInstance(ce, RClickChangePage)
			self.assertEqual(ce.action, RClickAction.change_page)
			self.assertEqual(ce.page, 123)

		self.__test_one(
			RClickChangePage(123),
			verifier=verify,
			json_1_7={'action': 'change_page', 'value': '123'},
			json_1_21_5={'action': 'change_page', 'page': 123},
		)

	def test_6_show_dialog(self):
		def verify(ce: RClickEvent):
			self.assertIsInstance(ce, RClickShowDialog)
			self.assertEqual(ce.action, RClickAction.show_dialog)
			self.assertEqual(ce.dialog, {'foo': 'bar'})

		self.__test_one(
			RClickShowDialog({'foo': 'bar'}),
			verifier=verify,
			json_1_7=None,  # not necessary to test it
			json_1_21_5={'action': 'show_dialog', 'dialog': {'foo': 'bar'}},
		)

	def test_7_custom(self):
		def verify(ce: RClickEvent):
			self.assertIsInstance(ce, RClickCustom)
			self.assertEqual(ce.action, RClickAction.custom)
			self.assertEqual(ce.id, 'foo:bar')
			self.assertEqual(ce.payload, {'abc': '123'})

		self.__test_one(
			RClickCustom(id='foo:bar', payload={'abc': '123'}),
			verifier=verify,
			json_1_7=None,  # not necessary to test it
			json_1_21_5={'action': 'custom', 'id': 'foo:bar', 'payload': {'abc': '123'}},
		)

	def test_8_rtext_api(self):
		text = RText('foo')

		js_1_7 = {'text': 'foo', 'clickEvent': {'action': 'suggest_command', 'value': '/say something'}}
		js_1_21_5 = {'text': 'foo', 'click_event': {'action': 'suggest_command', 'command': '/say something'}}

		text.set_click_event(RClickSuggestCommand('/say something'))
		self.assertEqual(text.to_json_object(json_format=RTextJsonFormat.V_1_7), js_1_7)
		self.assertEqual(text.to_json_object(json_format=RTextJsonFormat.V_1_21_5), js_1_21_5)

		self.assertEqual(text, RText('foo').set_click_event(RClickSuggestCommand('/say something')))
		self.assertEqual(text, RText('foo').set_click_event(RClickAction.suggest_command, '/say something'))
		self.assertEqual(text, RText('foo').c(RClickSuggestCommand('/say something')))
		self.assertEqual(text, RText('foo').c(RClickAction.suggest_command, '/say something'))


if __name__ == '__main__':
	unittest.main()
