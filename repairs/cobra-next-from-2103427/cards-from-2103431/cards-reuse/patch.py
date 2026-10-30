"""Exact Cobra-owned retained-Cards hook delta after the reviewed staged patches.

This module does not assemble, test, sign, run an APK or write source files.
The caller explicitly applies patch_activity to the matching staged Activity.
"""
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
APP = "Lcom/projectinfinity/kodi/InfinityLiveActivity;"
HELPER = "Lcom/projectinfinity/kodi/CobraCardsReuse;"
RENDER = "private cobraRenderGuideBrowser()V"
RESTYLE = "private cobraRestyleGuide()V"
RECENT = "private addRecent(Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;)V"
PREFIX_HOOKS = {
    "private persistSources()V": "sources",
    "private toggleFavorite(Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;)V": "favorites",
    "private reloadProfileCollections()V": "collections",
    "private hideCobraChannel(Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;)V": "hidden",
    "synthetic lambda$showCobraAddToGroup$74$com-projectinfinity-kodi-InfinityLiveActivity(Landroid/widget/EditText;Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;Landroid/content/DialogInterface;I)V": "custom",
}
INVENTORY_HOOKS = (
    ("private applyLoadResult(Lcom/projectinfinity/kodi/InfinityLiveActivity$LoadResult;)V", "p0", "v0"),
    ("private restoreCobraLibraryCache(Ljava/util/ArrayList;)Z", "v0", "v2"),
    ("synthetic lambda$confirmRemoveSource$96$com-projectinfinity-kodi-InfinityLiveActivity(Lcom/projectinfinity/kodi/InfinityLiveActivity$LiveSource;Landroid/content/DialogInterface;I)V", "p0", "p1"),
    ("synthetic lambda$loadAllEnabledSources$54$com-projectinfinity-kodi-InfinityLiveActivity(Ljava/util/ArrayList;ZLjava/util/ArrayList;Ljava/util/ArrayList;)V", "v0", "v7"),
)
METHOD_PATTERN = re.compile(r"^\.method ([^\n]+)\n.*?^\.end method", re.M | re.S)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _methods(text):
    matches = list(METHOD_PATTERN.finditer(text))
    result = {m[1]: m[0] + "\n" for m in matches}
    _require(len(result) == len(matches), "Duplicate Activity method signature")
    return result


def _entry(body, instructions):
    registers = re.compile(r"^    \.registers [0-9]+\n", re.M)
    matches = list(registers.finditer(body))
    _require(len(matches) == 1, "One original register declaration required")
    end = matches[0].end()
    return body[:end] + "\n" + instructions + body[end:]


def _one_arg(owner, name):
    return "    invoke-static/range {" + owner + " .. " + owner + "}, " + HELPER + "->" + name + "(Landroid/app/Activity;)V\n"


def patch_activity(text):
    """Return the reviewed twelve-method delta; reject every unrelated change."""
    budget = json.loads((HERE / "SOURCE-BUDGET.json").read_text())
    _require(_sha(text) == budget["input_source_sha256"], "Exact reviewed staged Activity required")
    _require(HELPER not in text, "Reuse hooks must not already be installed")
    before = _methods(text)
    selected = {RENDER, RESTYLE, RECENT, *PREFIX_HOOKS, *(row[0] for row in INVENTORY_HOOKS)}
    _require(len(selected) == 12, "Exact reviewed twelve-method selection required")
    _require(set(budget["allowed_changed_methods"]) == selected, "Reviewed method budget differs")
    _require(set(budget["selected_method_preimages"]) == selected, "Complete preimage vector required")
    _require(len(before) == budget["input_method_count"], "Original method count changed")
    metadata = METHOD_PATTERN.sub("", text)
    _require(_sha(metadata) == budget["class_metadata_sha256"], "Class metadata or fields changed")
    _require(all(budget["mutators_match_original431"].values()), "Original431 mutator preservation required")
    for signature, pin in budget["selected_method_preimages"].items():
        _require(signature in before and _sha(before[signature]) == pin, "Method preimage changed: " + signature)
    actual_inventory_budget = [
        {"method": signature, "owner_register": owner, "list_register": owned_list}
        for signature, owner, owned_list in INVENTORY_HOOKS
    ]
    _require(budget["inventory_clear_hooks"] == actual_inventory_budget, "Inventory publication aliases changed")

    revised = {}
    render = before[RENDER]
    label = "cobra_cards_reuse_original_browser"
    _require(label not in text, "Unique Cards reuse branch label required")
    early = (
        "    invoke-static/range {p0 .. p0}, " + HELPER + "->tryReuse(Landroid/app/Activity;)Z\n"
        "    move-result v0\n"
        "    if-eqz v0, :" + label + "\n"
        "    return-void\n\n"
        "    :" + label + "\n"
    )
    # v0 is redefined by the original first iget on the false path; no extra
    # register, field or call is added to the successful helper-owned return.
    render = _entry(render, early)
    installed_anchor = "    invoke-static/range {p0 .. p0}, Lcom/projectinfinity/kodi/CobraCardsLayout;->afterRender(Landroid/app/Activity;)V"
    _require(render.count(installed_anchor) == 2, "Two existing Render layout-completion hooks required")
    render = render.replace(installed_anchor, installed_anchor + "\n\n" + _one_arg("p0", "installed").rstrip("\n"))
    revised[RENDER] = render

    restyle = before[RESTYLE]
    shell_anchor = "    invoke-static/range {p0 .. p0}, Lcom/projectinfinity/kodi/CobraCardsLayout;->beforeShell(Landroid/app/Activity;)V"
    _require(restyle.count(shell_anchor) == 1, "One existing Restyle shell hook required")
    revised[RESTYLE] = restyle.replace(shell_anchor, shell_anchor + "\n\n" + _one_arg("p0", "beforeShell").rstrip("\n"), 1)

    # Observe only actual publication, not a failed restore or an early-return
    # callback. The list iget and clear retain their exact original instructions.
    for signature, owner, owned_list in INVENTORY_HOOKS:
        body = before[signature]
        load = "    iget-object " + owned_list + ", " + owner + ", " + APP + "->mChannels:Ljava/util/ArrayList;"
        clear = "    invoke-virtual {" + owned_list + "}, Ljava/util/ArrayList;->clear()V"
        anchor = load + "\n\n" + clear
        _require(body.count(anchor) == 1, "One actual inventory-clear publication required: " + signature)
        revised[signature] = body.replace(anchor, load + "\n\n" + _one_arg(owner, "inventory") + "\n" + clear, 1)

    for signature, helper_method in PREFIX_HOOKS.items():
        revised[signature] = _entry(before[signature], _one_arg("p0", helper_method))
    revised[RECENT] = _entry(
        before[RECENT],
        "    invoke-static/range {p0 .. p1}, " + HELPER + "->recent(Landroid/app/Activity;Ljava/lang/Object;)V\n",
    )

    _require(set(revised) == selected, "Incomplete selected hook implementation")
    result = text
    for signature in budget["allowed_changed_methods"]:
        old, new = before[signature], revised[signature]
        _require(old != new and result.count(old) == 1, "Exact unique method replacement required: " + signature)
        result = result.replace(old, new, 1)
    after = _methods(result)
    _require(set(before) == set(after), "No method additions or deletions allowed")
    _require({name for name in before if before[name] != after[name]} == selected, "Only selected method bodies may change")
    _require(METHOD_PATTERN.sub("", result) == metadata, "Fields/class metadata must remain exact")
    for signature in selected:
        get_registers = lambda body: re.findall(r"^    \.registers [0-9]+$", body, re.M)
        _require(get_registers(before[signature]) == get_registers(after[signature]), "Register budget changed: " + signature)
    _require(result.count(HELPER + "->") == 14, "Exact fourteen helper call sites required")
    _require(after[RENDER].count(HELPER + "->installed(") == 2, "Installed hooks belong only to Render")
    _require(all(HELPER + "->installed(" not in body for name, body in after.items() if name != RENDER), "No installed hook outside Render")
    return result
