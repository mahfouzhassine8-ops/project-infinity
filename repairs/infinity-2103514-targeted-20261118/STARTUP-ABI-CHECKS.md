# Selected ABI follow-up

Selective ELF inspection of the original signed 2103514 engine found the
five-argument `InfinityStartupTrace::Record` weak export, an exported
458752-byte trace slot array, and an exported 400-byte stage name array.
The diagnostic patch from 301a6cd0 would change the exported function
signature and array sizes. That run was stopped before full compilation.

Retain the original event and storage layout and preserve the five-argument
entry. Store the new IDs privately and publish them with the existing release
and acquire synchronization. Check the replacement's exact source delta,
interpreter and bookkeeping boundaries, NULL return, cancellation, bounded
overflow and canonical ID filtering. Verify both drain sink signatures.
Compile a host shared-library fixture and compare dynamic symbol names
and object sizes with the exact preimage. The real ARM64 gate compares
all default-visible exports, startup data sizes and shared dependencies
against signed 2103514. No physical or application execution is implied.

Run 44463352518 compiled and linked the complete engine. The ABI comparison
reported no missing exports, matching runtime dependencies and versions and
matching startup storage sizes. It rejected four new public formatting
templates caused by the ninth logger argument.

The follow-up keeps the existing eight logger arguments. The diagnostic
field is appended to a bounded local format buffer from a canonical ID
with braces excluded. Select a host fixture that compiles the production
log sink, requires the unchanged CLog template argument types, and compares
the exact format for a normal event and a create event. Use the unchanged
exact ARM64 ABI check again.
