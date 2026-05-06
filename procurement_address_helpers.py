from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


def _safe_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def get_taobao_address_form_locator_script() -> str:
    return r"""
() => {
    const normalize = (value) => (value || '').replace(/\s+/g, ' ').trim();
    const lower = (value) => normalize(value).toLowerCase();
    const isVisible = (node) => {
        if (!node || !(node instanceof HTMLElement)) return false;
        const style = window.getComputedStyle(node);
        if (!style || style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
        const rect = node.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
    };
    const normalizeNumber = (value, fallback = 0) => {
        const parsed = Number.parseFloat(String(value || ''));
        return Number.isFinite(parsed) ? parsed : fallback;
    };
    const getZIndex = (node) => {
        if (!node || !(node instanceof HTMLElement)) return 0;
        const style = window.getComputedStyle(node);
        return normalizeNumber(style?.zIndex, 0);
    };
    const isDialogText = (text) => {
        return text.includes('编辑地址') || text.includes('编辑收货地址') || text.includes('收货地址');
    };
    const findActiveDialogRoot = () => {
        const candidates = [];
        const nodes = Array.from(document.querySelectorAll('div, section, form, aside'));
        for (const node of nodes) {
            if (!isVisible(node)) continue;
            const text = normalize(node.innerText || node.textContent || '');
            if (!isDialogText(text)) continue;
            const controls = Array.from(node.querySelectorAll('input, textarea')).filter((item) => isVisible(item));
            if (controls.length < 3) continue;
            const rect = node.getBoundingClientRect();
            candidates.push({
                node,
                top: rect.top,
                left: rect.left,
                area: rect.width * rect.height,
                zIndex: getZIndex(node),
                controls: controls.length,
            });
        }
        candidates.sort((leftItem, rightItem) => {
            if (leftItem.zIndex !== rightItem.zIndex) return rightItem.zIndex - leftItem.zIndex;
            if (Math.abs(leftItem.area - rightItem.area) > 1) return rightItem.area - leftItem.area;
            if (Math.abs(leftItem.top - rightItem.top) > 6) return leftItem.top - rightItem.top;
            return leftItem.left - rightItem.left;
        });
        return candidates.length ? candidates[0].node : document.body;
    };
    const allControls = Array.from(document.querySelectorAll('input, textarea'));
    const modalRoot = findActiveDialogRoot();
    const rawControls = Array.from(modalRoot.querySelectorAll('input, textarea'));
    const isTextControl = (node) => {
        if (!node) return false;
        if (node instanceof HTMLTextAreaElement) return true;
        if (!(node instanceof HTMLInputElement)) return false;
        const type = (node.getAttribute('type') || 'text').toLowerCase();
        return ['', 'text', 'tel', 'search', 'number'].includes(type);
    };
    const visibleControls = rawControls.filter((node) => isVisible(node) && isTextControl(node));
    const getHints = (node) => lower([
        node.getAttribute('placeholder') || '',
        node.getAttribute('aria-label') || '',
        node.getAttribute('name') || '',
        node.getAttribute('id') || '',
        node.className || '',
    ].join(' '));
    const dedupe = (nodes) => {
        const seen = new Set();
        const results = [];
        for (const node of nodes) {
            if (!node || seen.has(node)) continue;
            seen.add(node);
            results.push(node);
        }
        return results;
    };
    const findIndex = (node) => allControls.indexOf(node);
    const labelMatches = (text, keywords) => keywords.some((keyword) => text.includes(keyword));
    const sortByPosition = (nodes) => {
        return [...nodes].sort((leftNode, rightNode) => {
            const leftRect = leftNode.getBoundingClientRect();
            const rightRect = rightNode.getBoundingClientRect();
            if (Math.abs(leftRect.top - rightRect.top) > 6) {
                return leftRect.top - rightRect.top;
            }
            return leftRect.left - rightRect.left;
        });
    };
    const describeNode = (node) => {
        if (!node) return '';
        return normalize([
            node.tagName || '',
            node.getAttribute?.('placeholder') || '',
            node.getAttribute?.('aria-label') || '',
            node.getAttribute?.('name') || '',
            node.getAttribute?.('id') || '',
            node.className || '',
        ].join(' '));
    };
    const collectNearbyControls = (startNode) => {
        const results = [];
        let current = startNode;
        for (let depth = 0; depth < 7 && current; depth += 1) {
            const parent = current.parentElement;
            if (parent) {
                const scoped = Array.from(parent.querySelectorAll('input, textarea')).filter((item) => isVisible(item) && isTextControl(item));
                results.push(...scoped);
            }
            current = parent;
        }
        return dedupe(results);
    };
    const getFieldRow = (keywords, excludeKeywords = []) => {
        const rows = [];
        const seen = new Set();
        const textNodes = Array.from(modalRoot.querySelectorAll('label, span, div, dt, dd, p, strong'));
        for (const node of textNodes) {
            if (!isVisible(node)) continue;
            const text = normalize(node.textContent || node.innerText || '');
            if (!labelMatches(text, keywords)) continue;
            if (excludeKeywords.length && labelMatches(text, excludeKeywords)) continue;
            let current = node;
            for (let depth = 0; depth < 6 && current; depth += 1) {
                const controls = sortByPosition(Array.from(current.querySelectorAll('input, textarea')).filter((item) => isVisible(item) && isTextControl(item)));
                const rect = current.getBoundingClientRect();
                if (controls.length >= 1 && controls.length <= 4 && rect.width >= 180 && rect.height >= 20) {
                    if (!seen.has(current)) {
                        seen.add(current);
                        rows.push(current);
                    }
                    break;
                }
                current = current.parentElement;
            }
        }
        const sortedRows = sortByPosition(rows);
        return sortedRows.length ? sortedRows[0] : null;
    };
    const getRowControls = (row) => {
        if (!row) return [];
        return sortByPosition(Array.from(row.querySelectorAll('input, textarea')).filter((item) => isVisible(item) && isTextControl(item)));
    };
    const collectByLabel = (keywords, excludeKeywords = []) => {
        const labeled = [];
        const textNodes = Array.from(modalRoot.querySelectorAll('label, span, div, dt, dd, p, strong'));
        for (const node of textNodes) {
            if (!isVisible(node)) continue;
            const text = normalize(node.textContent || node.innerText || '');
            if (!labelMatches(text, keywords)) continue;
            if (excludeKeywords.length && labelMatches(text, excludeKeywords)) continue;
            labeled.push(...collectNearbyControls(node));
        }
        return sortByPosition(dedupe(labeled));
    };
    const collectByHint = (keywords) => visibleControls.filter((node) => keywords.some((keyword) => getHints(node).includes(keyword)));
    const rankByPreference = (nodes, tester) => {
        const preferred = [];
        const others = [];
        for (const node of nodes) {
            if (tester(node)) {
                preferred.push(node);
            } else {
                others.push(node);
            }
        }
        return [...preferred, ...others];
    };
    const pickAddressControls = () => {
        const addressRow = getFieldRow(['详细地址'], ['地址信息']);
        const rowControls = getRowControls(addressRow);
        if (rowControls.length) {
            return rowControls;
        }
        const exactCandidates = collectByLabel(['详细地址'], ['地址信息']);
        const fallbackCandidates = collectByLabel(['收货地址', '收件地址', '地址'], ['地址信息']);
        const hintedCandidates = collectByHint(['详细地址', '街道', '门牌', '地址']);
        const candidates = rankByPreference(dedupe([
            ...exactCandidates,
            ...fallbackCandidates,
            ...hintedCandidates,
            ...visibleControls.filter((node) => node instanceof HTMLTextAreaElement),
        ]), (node) => node instanceof HTMLTextAreaElement || getHints(node).includes('地址'));
        return candidates;
    };
    const pickNameControls = () => {
        const nameRow = getFieldRow(['收货人姓名', '收件人姓名']);
        const rowControls = getRowControls(nameRow);
        if (rowControls.length) {
            return rowControls;
        }
        return rankByPreference(dedupe([
            ...collectByLabel(['收货人姓名', '收件人姓名']),
            ...collectByLabel(['收货人', '收件人', '姓名']),
            ...collectByHint(['收货人', '收件人', '姓名']),
        ]), (node) => {
            const hints = getHints(node);
            return hints.includes('姓名') || hints.includes('收货人') || hints.includes('收件人');
        });
    };
    const pickPhoneControls = () => {
        const phoneRow = getFieldRow(['手机号码', '手机号', '手机']);
        const rowControls = getRowControls(phoneRow).filter((node) => node instanceof HTMLInputElement);
        if (rowControls.length >= 2) {
            return [rowControls[rowControls.length - 1], ...rowControls.slice(0, -1)];
        }
        if (rowControls.length === 1) {
            return rowControls;
        }
        const labeled = collectByLabel(['手机号码', '手机号', '手机'], ['联系电话']);
        const hinted = collectByHint(['手机', '手机号', '电话', 'mobile', 'phone']);
        const numericInputs = visibleControls.filter((node) => {
            if (!(node instanceof HTMLInputElement)) {
                return false;
            }
            const inputMode = lower(node.getAttribute('inputmode') || '');
            const type = lower(node.getAttribute('type') || '');
            const hints = getHints(node);
            const maxLength = Number.parseInt(node.getAttribute('maxlength') || '0', 10);
            return type === 'tel'
                || inputMode.includes('numeric')
                || hints.includes('手机')
                || hints.includes('电话')
                || maxLength === 11;
        });
        const candidates = sortByPosition(dedupe([...labeled, ...hinted, ...numericInputs]));
        const textInputs = candidates.filter((node) => node instanceof HTMLInputElement);
        if (textInputs.length >= 2) {
            return [textInputs[textInputs.length - 1], ...textInputs.slice(0, -1)];
        }
        if (candidates.length >= 2) {
            return [candidates[candidates.length - 1], ...candidates.slice(0, -1)];
        }
        return candidates;
    };
    const addressControls = pickAddressControls();
    const nameControls = pickNameControls();
    const phoneControls = pickPhoneControls();
    return {
        modal_found: modalRoot !== document.body,
        address_candidates: addressControls.map((node) => findIndex(node)).filter((index) => index >= 0),
        name_candidates: nameControls.map((node) => findIndex(node)).filter((index) => index >= 0),
        phone_candidates: phoneControls.map((node) => findIndex(node)).filter((index) => index >= 0),
        address_debug: addressControls.map((node) => ({ index: findIndex(node), desc: describeNode(node) })),
        name_debug: nameControls.map((node) => ({ index: findIndex(node), desc: describeNode(node) })),
        phone_debug: phoneControls.map((node) => ({ index: findIndex(node), desc: describeNode(node) })),
    };
}
"""


def fill_taobao_address_form_control(frame: Any, selector_index: int, value: str, field_name: str = "") -> bool:
    if selector_index < 0:
        return False
    target_value = _safe_text(value)
    if not target_value:
        return False
    locator = frame.locator("input, textarea").nth(selector_index)
    try:
        locator.wait_for(state="visible", timeout=2500)
    except Exception:
        return False
    try:
        locator.scroll_into_view_if_needed(timeout=2000)
    except Exception:
        pass
    try:
        locator.hover(timeout=2000)
    except Exception:
        pass
    try:
        locator.focus(timeout=1500)
    except Exception:
        pass
    try:
        locator.click(timeout=2000)
    except Exception:
        pass
    try:
        locator.fill(target_value, timeout=2500)
    except Exception:
        try:
            locator.press("Control+A", timeout=1500)
        except Exception:
            pass
        try:
            locator.press("Backspace", timeout=1500)
        except Exception:
            pass
        try:
            locator.type(target_value, delay=20, timeout=4000)
        except Exception:
            try:
                locator.evaluate(
                    """
                    (node, nextValue) => {
                        const value = String(nextValue || '');
                        const prototype = node instanceof HTMLTextAreaElement
                            ? HTMLTextAreaElement.prototype
                            : HTMLInputElement.prototype;
                        const setter = Object.getOwnPropertyDescriptor(prototype, 'value')?.set;
                        if (setter) {
                            setter.call(node, value);
                        } else {
                            node.value = value;
                        }
                        node.dispatchEvent(new Event('input', { bubbles: true }));
                        node.dispatchEvent(new Event('change', { bubbles: true }));
                        node.dispatchEvent(new Event('blur', { bubbles: true }));
                    }
                    """,
                    target_value,
                )
            except Exception:
                return False
    try:
        current_value = _safe_text(locator.input_value(timeout=1500))
    except Exception:
        try:
            current_value = _safe_text(locator.evaluate("node => node.value || ''"))
        except Exception:
            current_value = ""
    return bool(current_value) and target_value.replace(" ", "") in current_value.replace(" ", "")


def fill_taobao_address_form_from_candidates(frame: Any, candidate_indexes: Any, value: str, field_name: str) -> bool:
    indexes: List[int] = []
    for item in candidate_indexes or []:
        candidate_index = _to_int(item, -1)
        if candidate_index >= 0 and candidate_index not in indexes:
            indexes.append(candidate_index)
    for candidate_index in indexes:
        if fill_taobao_address_form_control(frame, candidate_index, value, field_name=field_name):
            return True
    return False


def attempt_taobao_address_form_fill(
    page: Any,
    recipient_info: Dict[str, str],
    iter_frames: Callable[[Any], List[Any]],
    get_latest_page: Callable[[Any, Any], Any],
    append_log: Callable[[str], None],
) -> Dict[str, Any]:
    locate_script = get_taobao_address_form_locator_script()
    try:
        context = page.context
    except Exception:
        context = None
    target_page = page
    last_controls: Dict[str, Any] = {}
    last_fill_result = {"address": False, "name": False, "phone": False}
    for _ in range(12):
        if context is not None:
            target_page = get_latest_page(context, target_page)
        for frame in iter_frames(target_page):
            try:
                controls = frame.evaluate(locate_script) or {}
            except Exception:
                continue
            last_controls = controls
            address_ok = fill_taobao_address_form_from_candidates(frame, controls.get("address_candidates"), _safe_text(recipient_info.get("address")), "详细地址")
            name_ok = fill_taobao_address_form_from_candidates(frame, controls.get("name_candidates"), _safe_text(recipient_info.get("name")), "收货人姓名")
            phone_ok = fill_taobao_address_form_from_candidates(frame, controls.get("phone_candidates"), _safe_text(recipient_info.get("phone")), "手机号码")
            last_fill_result = {"address": address_ok, "name": name_ok, "phone": phone_ok}
            if address_ok and name_ok and phone_ok:
                return {
                    "success": True,
                    "address": address_ok,
                    "name": name_ok,
                    "phone": phone_ok,
                    "controls": controls,
                }
        try:
            target_page.wait_for_timeout(700)
        except Exception:
            break
    append_log(
        "淘宝编辑地址模态窗自动填入失败："
        f"modal_found={_safe_text(last_controls.get('modal_found'))}; "
        f"address_candidates={_safe_text(last_controls.get('address_debug'))}; "
        f"name_candidates={_safe_text(last_controls.get('name_debug'))}; "
        f"phone_candidates={_safe_text(last_controls.get('phone_debug'))}; "
        f"fill_result={last_fill_result}"
    )
    return {
        "success": False,
        "address": bool(last_fill_result.get("address")),
        "name": bool(last_fill_result.get("name")),
        "phone": bool(last_fill_result.get("phone")),
        "controls": last_controls,
    }


def format_recipient_summary(recipient_info: Dict[str, str]) -> str:
    address = _safe_text(recipient_info.get("address"))
    phone = _safe_text(recipient_info.get("phone"))
    name = _safe_text(recipient_info.get("name"))
    return " , ".join([item or "-" for item in [address, phone, name]])


def build_recipient_copy_items(recipient_info: Dict[str, str]) -> List[Dict[str, str]]:
    return [
        {"label": "复制地址", "value": _safe_text(recipient_info.get("address"))},
        {"label": "复制姓名", "value": _safe_text(recipient_info.get("name"))},
        {"label": "复制电话", "value": _safe_text(recipient_info.get("phone"))},
    ]


def get_failed_recipient_fields(field_result: Optional[Dict[str, Any]]) -> List[str]:
    result = field_result or {}
    failed_fields: List[str] = []
    if not bool(result.get("address")):
        failed_fields.append("地址")
    if not bool(result.get("name")):
        failed_fields.append("姓名")
    if not bool(result.get("phone")):
        failed_fields.append("手机")
    return failed_fields


def build_feedback_plan(payload: Optional[Dict[str, Any]], operation: str = "purchase", error: Optional[BaseException] = None) -> Dict[str, Any]:
    payload = payload or {}
    field_result = payload.get("address_fill_result") or {}
    failed_fields = get_failed_recipient_fields(field_result if field_result else {"address": False, "name": False, "phone": False})
    failed_fields_text = "、".join(failed_fields) if failed_fields else "无"

    if error is not None:
        return {
            "severity": "warning",
            "title": "提示",
            "message": "已尝试重新执行收货信息填写，但采购浏览器阶段失败。系统已把收货信息复制到剪贴板，请手动继续。"
            if operation == "address_retry"
            else "已尝试用可控采购浏览器打开宝贝页，但自动点击“立刻购买”失败。系统已把收货信息复制到剪贴板，请手动继续。",
            "status_text": "地址填写状态：执行失败（浏览器阶段）",
            "failed_fields": failed_fields,
            "failed_fields_text": failed_fields_text,
            "copy_required": True,
        }

    address_ok = bool(payload.get("address_form_filled"))
    clicked = bool(payload.get("clicked"))
    edit_clicked = bool(payload.get("address_edit_clicked"))
    has_login_state = bool(payload.get("has_login_state"))

    if clicked and edit_clicked and address_ok:
        return {
            "severity": "info",
            "title": "已完成重试" if operation == "address_retry" else "已开始采购",
            "message": "已重新打开购买页，并再次完成收货信息自动填写。后续步骤请手动确认。"
            if operation == "address_retry"
            else "已打开宝贝页，自动点击“立刻购买”，已定位第二个地址点击“编辑”，并已自动填入地址信息、收货人姓名和手机号码。后续步骤请手动处理。",
            "status_text": "地址填写状态：已完成自动填写",
            "failed_fields": [],
            "failed_fields_text": "无",
            "copy_required": False,
        }

    if clicked and edit_clicked:
        return {
            "severity": "warning",
            "title": "提示",
            "message": f"已重新进入地址编辑，但仍未完成 {failed_fields_text} 自动填写。系统已把收货信息复制到剪贴板，请直接粘贴补全。"
            if operation == "address_retry"
            else f"已打开宝贝页，自动点击“立刻购买”，并已定位第二个地址点击“编辑”，但未完成 {failed_fields_text} 自动填写。系统已把收货信息复制到剪贴板，请手动继续。",
            "status_text": f"地址填写状态：未完成（失败项：{failed_fields_text}）",
            "failed_fields": failed_fields,
            "failed_fields_text": failed_fields_text,
            "copy_required": True,
        }

    if clicked:
        return {
            "severity": "warning",
            "title": "提示",
            "message": "已重新进入购买页，但未找到可编辑的收货地址入口。系统已把收货信息复制到剪贴板，请手动继续。"
            if operation == "address_retry"
            else "已打开宝贝页并自动点击“立刻购买”，但未完成第二个地址“编辑”。系统已把收货信息复制到剪贴板，请手动继续。",
            "status_text": "地址填写状态：未进入地址编辑",
            "failed_fields": failed_fields,
            "failed_fields_text": failed_fields_text,
            "copy_required": True,
        }

    if not has_login_state:
        return {
            "severity": "warning",
            "title": "提示",
            "message": "已用可控采购浏览器打开宝贝页，但当前没有可复用的淘宝登录态，未继续自动点击“立刻购买”。请先登录后手动继续，或先点击“一键获取登录态”。",
            "status_text": "地址填写状态：未进入购买流程（缺少登录态）",
            "failed_fields": failed_fields,
            "failed_fields_text": failed_fields_text,
            "copy_required": False,
        }

    return {
        "severity": "warning",
        "title": "提示",
        "message": "已重新打开宝贝页，但未进入购买页，因此无法执行收货信息重试填写。系统已把收货信息复制到剪贴板，请手动继续。"
        if operation == "address_retry"
        else "已打开宝贝页，但未找到“立刻购买”按钮。系统已把收货信息复制到剪贴板，请手动继续。",
        "status_text": "地址填写状态：未进入购买页",
        "failed_fields": failed_fields,
        "failed_fields_text": failed_fields_text,
        "copy_required": operation == "address_retry" or not has_login_state,
    }