import { e as t, f as i, g as s, h as d } from "./url-68a935bf.js";
import { b as c } from "./__uno-bcdf16b1.js";
var p = function p() {
    var e = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : !1;
    if (e) {
      window && (window.location.href = t);
      return;
    }
    window == null || window.open(t);
  },
  w = function w(e) {
    var o, n;
    window == null || window.open(d), (n = (o = window == null ? void 0 : window.top) == null ? void 0 : o.postMessage) == null || n.call(o, {
      type: "dwEvent",
      action: "click_feedback",
      page: e
    }, "*");
  },
  f = function f(e) {
    var o = e;
    if (o.cropid) {
      window == null || window.open(i + "".concat(o.cropid, "/").concat(o.groupid, "/").concat(o.fid));
      return;
    }
    window == null || window.open(s + e.fid);
  },
  g = function g(e) {
    return c.runtime.getURL("kdocs/".concat(e, "/index.html"));
  };
export { p as a, f as b, w as c, g };
