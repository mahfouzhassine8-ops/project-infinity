"""Adversarial host tests of recipe trust boundaries, not app/device tests."""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
import apply as recipe


class RecipeGuards(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='cobra205-recipe-guards-')
        self.root = Path(self.temporary.name)
        (self.root / 'tests').mkdir()
        self.test_name = 'tests/Cobra2103206GuardTest.java'
        (self.root / self.test_name).write_text('fixture-test\n')
        (self.root / 'features.patch').write_text('fixture-patch\n')
        (self.root / 'parent-png-pixels.json').write_text('{}\n')
        self.review = {
            'status': 'frozen', 'parent_build': 2103205, 'parent_commit': recipe.PARENT_COMMIT,
            'files': {recipe.ACTIVITY: {'before': 'old', 'after': 'new'}},
            'patch_sha256': recipe.sha(self.root / 'features.patch'),
            'parent_png_pixels_sha256': recipe.sha(self.root / 'parent-png-pixels.json'),
            'test_source_hashes': {self.test_name: recipe.sha(self.root / self.test_name)},
            'inherited_android_cases': 637, 'parent_source_files': 226, 'new_source_files': 0,
        }
        self.patcher = patch.object(recipe, 'ROOT', self.root)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temporary.cleanup()

    def check(self):
        (self.root / 'reviewed.json').write_text(json.dumps(self.review))
        return recipe.checked_review()

    def reject(self, phrase):
        with self.assertRaisesRegex(RuntimeError, phrase):
            self.check()

    def testFrozenContractAcceptsItsExactFixture(self):
        self.assertEqual(self.check(), self.review)

    def testUnfrozenRecipeCannotRun(self):
        self.review['status'] = 'pending'
        self.reject('blocked until review')

    def testWrongParentBuildRejected(self):
        self.review['parent_build'] = 2103203
        self.reject('Wrong reviewed parent')

    def testWrongParentCommitRejected(self):
        self.review['parent_commit'] = '0' * 40
        self.reject('Wrong reviewed parent')

    def testPatchDigestDriftRejected(self):
        (self.root / 'features.patch').write_text('changed\n')
        self.reject('patch digest drift')

    def testParentPngPixelContractDriftRejected(self):
        (self.root / 'parent-png-pixels.json').write_text('{"replaced":"pixel contract"}\n')
        self.reject('parent PNG pixel contract drift')

    def testTestSourceDriftRejected(self):
        (self.root / self.test_name).write_text('weakened\n')
        self.reject('test drift')

    def testEmptyNewTestsRejected(self):
        self.review['test_source_hashes'] = {}
        self.reject('No frozen feature regressions')

    def testEscapingTestPathRejected(self):
        self.review['test_source_hashes'] = {'tests/../outside.java': 'abc'}
        self.reject('Invalid frozen test path')

    def testNoInheritedCaseCountReduction(self):
        self.review['inherited_android_cases'] = 499
        self.reject('Inherited identity count drift')

    def testNoParentInventoryReduction(self):
        self.review['parent_source_files'] = 219
        self.reject('Parent source inventory drift')

    def testNewFilesMustMatchDeclaredCount(self):
        self.review['files']['tools/android/packaging/xbmc/src/CobraGuard.java.in'] = {'before': None, 'after': 'new'}
        self.reject('Added file count drift')

    def testExistingNativeSourceCannotBeAllowed(self):
        self.review['files']['xbmc/cores/VideoPlayer.cpp'] = {'before': 'old', 'after': 'new'}
        self.reject('Unreviewed source owner')

    def testManifestCannotBeChanged(self):
        self.assertFalse(recipe.permitted_file('tools/android/packaging/xbmc/AndroidManifest.xml.in', 'old'))

    def testOnlyNewCobraTopLevelJavaHelpersAllowed(self):
        self.assertTrue(recipe.permitted_file('tools/android/packaging/xbmc/src/CobraGuard.java.in', None))
        for name in ['media/icon.png', 'tools/android/packaging/xbmc/src/Else.java.in',
                     'tools/android/packaging/xbmc/src/../CobraGuard.java.in',
                     'tools/android/packaging/xbmc/src/content/CobraGuard.java.in']:
            self.assertFalse(recipe.permitted_file(name, None), name)

    def testAppendOnlyCmakeRegistrationAccepted(self):
        suffix = '\nconfigure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraGuard.java.in\n' \
                 '               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraGuard.java @ONLY)\n'
        recipe.validate_install('original\n', 'original\n' + suffix,
                                ['tools/android/packaging/xbmc/src/CobraGuard.java.in'])

    def testOldCmakeInstructionsCannotChange(self):
        with self.assertRaisesRegex(RuntimeError, 'append-only'):
            recipe.validate_install('original\n', 'modified\n', [])

    def testCmakeCannotStartNativeBuild(self):
        with self.assertRaisesRegex(RuntimeError, 'Unexpected added CMake'):
            recipe.validate_install('original\n', 'original\nadd_subdirectory(xbmc)\n', [])

    def testUnregisteredHelperRejected(self):
        with self.assertRaisesRegex(RuntimeError, 'registration mismatch'):
            recipe.validate_install('original\n', 'original\n',
                                    ['tools/android/packaging/xbmc/src/CobraGuard.java.in'])

    def testCmakeCannotConfigureUnaddedHelper(self):
        suffix = '\nconfigure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraGuard.java.in\n' \
                 '               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraGuard.java @ONLY)\n'
        with self.assertRaisesRegex(RuntimeError, 'registration mismatch'):
            recipe.validate_install('original\n', 'original\n' + suffix, [])

    def testWrongCmakeDestinationRejected(self):
        suffix = '\nconfigure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraGuard.java.in\n' \
                 '               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/Main.java @ONLY)\n'
        with self.assertRaisesRegex(RuntimeError, 'Unexpected added CMake'):
            recipe.validate_install('original\n', 'original\n' + suffix,
                                    ['tools/android/packaging/xbmc/src/CobraGuard.java.in'])


class ParentImageGates(unittest.TestCase):
    def setUp(self):
        from PIL import Image
        self.temporary = tempfile.TemporaryDirectory(prefix='cobra205-parent-image-guards-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.image = self.source / 'media/fixture.png'
        self.image.parent.mkdir(parents=True)
        self.install = self.source / recipe.INSTALL
        self.install.parent.mkdir(parents=True)
        self.install.write_text('original cmake\n')
        Image.new('RGBA', (3, 2), (10, 20, 30, 255)).save(self.image)
        self.expected = recipe.source_inventory(self.source)
        with Image.open(self.image) as picture:
            decoded = {'size': list(picture.size),
                       'rgba_sha256': hashlib.sha256(picture.convert('RGBA').tobytes()).hexdigest()}
        (self.root / 'parent-png-pixels.json').write_text(json.dumps({'media/fixture.png': decoded}))
        self.patcher = patch.object(recipe, 'ROOT', self.root)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def testIdenticalParentBytesPass(self):
        actual, variations = recipe.verify_parent_inventory(self.source, self.expected)
        self.assertEqual(actual, self.expected)
        self.assertEqual(variations, [])

    def testOnlyPngMetadataVarianceAccepted(self):
        from PIL import Image, PngImagePlugin
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text('generation-time', 'changed metadata only')
        Image.new('RGBA', (3, 2), (10, 20, 30, 255)).save(self.image, pnginfo=metadata)
        actual, variations = recipe.verify_parent_inventory(self.source, self.expected)
        self.assertNotEqual(actual['media/fixture.png'], self.expected['media/fixture.png'])
        self.assertEqual(variations, ['media/fixture.png'])

    def testSingleChangedPixelRejected(self):
        from PIL import Image
        picture = Image.new('RGBA', (3, 2), (10, 20, 30, 255))
        picture.putpixel((2, 1), (11, 20, 30, 255))
        picture.save(self.image)
        with self.assertRaisesRegex(RuntimeError, 'PNG pixels/dimensions changed'):
            recipe.verify_parent_inventory(self.source, self.expected)

    def testChangedImageDimensionsRejected(self):
        from PIL import Image
        Image.new('RGBA', (2, 3), (10, 20, 30, 255)).save(self.image)
        with self.assertRaisesRegex(RuntimeError, 'PNG pixels/dimensions changed'):
            recipe.verify_parent_inventory(self.source, self.expected)

    def testChangedNonPngBytesRejected(self):
        self.install.write_text('changed cmake\n')
        with self.assertRaisesRegex(RuntimeError, 'Complete parent source input drift'):
            recipe.verify_parent_inventory(self.source, self.expected)

    def testAddedParentInputRejected(self):
        (self.image.parent / 'unreviewed.txt').write_text('extra')
        with self.assertRaisesRegex(RuntimeError, 'Complete parent source inventory drift'):
            recipe.verify_parent_inventory(self.source, self.expected)

    def testRemovedParentInputRejected(self):
        self.image.unlink()
        with self.assertRaisesRegex(RuntimeError, 'Complete parent source inventory drift'):
            recipe.verify_parent_inventory(self.source, self.expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
