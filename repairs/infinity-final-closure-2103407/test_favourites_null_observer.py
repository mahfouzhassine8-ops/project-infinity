import ast
from types import SimpleNamespace
import unittest
import favourites_null_observer as adapter


class NativeFavouritesObservationTests(unittest.TestCase):
    def proxy(self,value,mode='final-actions'):
        calls=[];result={}
        actual=SimpleNamespace(rpc=lambda *args:(calls.append(args) or value),require='original assertion')
        scope=dict(ui=actual,mode=mode,result=result)
        exec('if True:\n'+adapter.BLOCK,scope)
        return scope['ui'],actual,calls,result

    def test_null_is_empty_only_with_actual_exact_native_zero_limits(self):
        raw=dict(favourites=None,limits=dict(start=0,end=0,total=0))
        ui,actual,calls,result=self.proxy(raw)
        self.assertEqual(ui.rpc('Favourites.GetFavourites',{'properties':['path']}),dict(raw,favourites=[]))
        self.assertIsNone(raw['favourites']);self.assertEqual(result['raw_native_favourites'],[raw])
        self.assertEqual(calls,[('Favourites.GetFavourites',{'properties':['path']})])
        for invalid in (None,{},dict(favourites='bad'),dict(favourites=[None]),dict(favourites=None),
                        dict(raw,limits=dict(start=0,end=0,total=1)),dict(raw,limits=dict(start=False,end=0,total=0))):
            with self.assertRaises(RuntimeError):self.proxy(invalid)[0].rpc('Favourites.GetFavourites')

    def test_nonempty_rows_all_other_methods_and_unselected_modes_are_unchanged(self):
        raw=dict(favourites=[dict(path='exact native source')]);ui,actual,calls,result=self.proxy(raw)
        self.assertIs(ui.rpc('Favourites.GetFavourites'),raw)
        self.assertIs(ui.rpc('Input.Select'),raw);self.assertEqual(ui.require,'original assertion')
        ui,actual,_,_=self.proxy(raw,mode='final-continue');self.assertIs(ui,actual)

    def test_full_inverse_and_each_original_assertion_ast_unchanged(self):
        from android17_reference_observation import OLD
        text=(OLD/'tracking/final-eight/android_selected.py').read_text()
        updated=adapter.instrument(text);self.assertEqual(adapter.restore(updated),text)
        def predicates(raw):
            return [ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(raw)) if isinstance(n,ast.Call)
                    and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name)
                    and n.func.value.id=='ui' and n.func.attr=='require']
        self.assertEqual(predicates(updated),predicates(text))


if __name__=='__main__':unittest.main(verbosity=2)
