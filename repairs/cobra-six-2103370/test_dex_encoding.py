import unittest
from dex_encoding import canonical
class DexEncodingProofTest(unittest.TestCase):
 def body(self,opcode='const-string',value='writer',target='cond_4',jump='cond_4',register='v0',padding=''):
  return '.class LExample;\n.method public run()V\n.registers 2\n    '+opcode+' '+register+', "'+value+'"\n    if-eqz v0, :'+jump+'\n    sparse-switch v0, :data_8\n    :'+target+'\n    return-void\n'+padding+'    :data_8\n    .sparse-switch\n        0x1 -> :'+target+'\n    .end sparse-switch\n.end method\n'
 def test_string_width_and_address_labels_preserve_exact_graph(self):
  self.assertEqual(canonical(self.body()),canonical(self.body(opcode='const-string/jumbo',target='cond_5',jump='cond_5')))
 def test_changed_literal_and_register_are_rejected(self):
  self.assertNotEqual(canonical(self.body()),canonical(self.body(value='different')))
  self.assertNotEqual(canonical(self.body()),canonical(self.body(register='v1')))
 def test_changed_branch_and_exception_targets_are_rejected(self):
  before=self.body().replace('    return-void','    :other\n    return-void')
  self.assertNotEqual(canonical(before),canonical(before.replace('if-eqz v0, :cond_4','if-eqz v0, :other')))
 def test_only_unreachable_switch_alignment_nop_can_be_ignored(self):
  self.assertEqual(canonical(self.body()),canonical(self.body(padding='    nop\n')))
  self.assertNotEqual(canonical(self.body()),canonical(self.body().replace('    sparse-switch','    nop\n    sparse-switch')))
 def test_label_shaped_string_literal_is_never_rewritten(self):
  value=self.body(value=':cond_4');self.assertIn('":cond_4"',canonical(value))
if __name__=='__main__':unittest.main()
