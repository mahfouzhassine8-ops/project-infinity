"""Focused selector regressions for the real Search101 UI control contract."""
import unittest
from xml.etree.ElementTree import Element
import android_search_input as inputs
import importlib.util
from pathlib import Path
from urllib.parse import urlencode

spec=importlib.util.spec_from_file_location('selected_search_checks',Path(__file__).resolve().parents[1]/'tracking/final-eight/android_selected.py')
selected=importlib.util.module_from_spec(spec);spec.loader.exec_module(selected)


def node(text='', kind='android.widget.TextView', description='', enabled=True, clickable=True):
    return Element('node', {'text':text, 'class':kind, 'content-desc':description,
        'enabled':str(enabled).lower(), 'clickable':str(clickable).lower()})


class SearchInputContract(unittest.TestCase):
    def test_reference_search_all_is_ready_after_label_changes(self):
        edit=node('The Matrix','android.widget.EditText')
        submit=node('Search All')
        self.assertIs(inputs.editor_node([edit,submit]),edit)
        self.assertIs(inputs.submit_node([edit,submit],'all'),submit)

    def test_reference_selected_provider_textview_is_button_target(self):
        submit=node('Search POV')
        self.assertIs(inputs.submit_node([node('POV'),submit],'plugin.video.pov'),submit)

    def test_selector_uses_post_selection_content_description(self):
        provider=node('','android.widget.LinearLayout','POV, select provider')
        self.assertIs(inputs.provider_node([provider],'POV'),provider)
        provider.set('content-desc','POV, selected')
        self.assertIs(inputs.provider_node([provider],'POV'),provider)

    def test_disabled_duplicate_wrong_provider_and_plain_labels_are_rejected(self):
        self.assertIsNone(inputs.submit_node([node('Search POV',clickable=False)]))
        self.assertIsNone(inputs.submit_node([node('Search POV',enabled=False)]))
        self.assertIsNone(inputs.submit_node([node('Search All')],'plugin.video.pov'))
        self.assertIsNone(inputs.submit_node([node('Search All'),node('Search All')]))
        self.assertIsNone(inputs.provider_node([node('','android.widget.LinearLayout','POV, select provider',False)],'POV'))

    def test_accessibility_contract_supports_specialty_search_label(self):
        submit=node('Search Anime Provider',description='Submit Infinity Search')
        self.assertIs(inputs.submit_node([submit]),submit)


class SearchResultContract(unittest.TestCase):
    def route(self,**changes):
        params=dict(action='search-provider',media='movie',query='The Matrix',provider='plugin.video.pov')
        params.update(changes)
        return 'plugin://script.infinity.commandcenter/?'+urlencode({k:v for k,v in params.items() if v is not None})

    def test_single_provider_exact_identity_and_attribution(self):
        records=[{'tmdb':'','provider':'plugin.video.pov'},{'tmdb':'603','provider':'plugin.video.pov'}]
        for case in ('final-search-pov-enter','final-search-pov-button'):
            self.assertTrue(selected.search_results_match(case,self.route(),records))

    def test_wrong_query_category_provider_or_dispatch_is_rejected(self):
        records=[{'tmdb':'603','provider':'plugin.video.pov'}]
        for change in ({'provider':'plugin.video.seren'},{'media':'tv'},{'query':'Matrix Reloaded'},{'action':'search-all'}):
            self.assertFalse(selected.search_results_match('final-search-pov-enter',self.route(**change),records))

    def test_wrong_identity_unattributed_or_foreign_result_is_rejected(self):
        for records in ([{'tmdb':'604','provider':'plugin.video.pov'}],
                        [{'tmdb':'603','provider':''}],
                        [{'tmdb':'603','provider':'plugin.video.pov'},{'tmdb':'603','provider':'plugin.video.seren'}]):
            self.assertFalse(selected.search_results_match('final-search-pov-enter',self.route(),records))

    def test_all_requires_each_fixture_provider_and_exact_search_all_route(self):
        records=[{'tmdb':'603','provider':aid} for aid in ('plugin.video.pov','plugin.video.umbrella','plugin.video.seren')]
        route=self.route(action='search-all',provider=None)
        self.assertTrue(selected.search_results_match('final-search-all-enter',route,records))
        self.assertFalse(selected.search_results_match('final-search-all-enter',route,records[:2]))
        self.assertFalse(selected.search_results_match('final-search-all-enter',self.route(),records))


if __name__=='__main__':unittest.main()
