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
