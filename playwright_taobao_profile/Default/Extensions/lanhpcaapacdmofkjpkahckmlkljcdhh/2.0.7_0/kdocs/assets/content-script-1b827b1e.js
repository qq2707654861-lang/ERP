function _createForOfIteratorHelper(o, allowArrayLike) { var it = typeof Symbol !== "undefined" && o[Symbol.iterator] || o["@@iterator"]; if (!it) { if (Array.isArray(o) || (it = _unsupportedIterableToArray(o)) || allowArrayLike && o && typeof o.length === "number") { if (it) o = it; var i = 0; var F = function F() {}; return { s: F, n: function n() { if (i >= o.length) return { done: true }; return { done: false, value: o[i++] }; }, e: function e(_e3) { throw _e3; }, f: F }; } throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); } var normalCompletion = true, didErr = false, err; return { s: function s() { it = it.call(o); }, n: function n() { var step = it.next(); normalCompletion = step.done; return step; }, e: function e(_e4) { didErr = true; err = _e4; }, f: function f() { try { if (!normalCompletion && it.return != null) it.return(); } finally { if (didErr) throw err; } } }; }
function _get() { if (typeof Reflect !== "undefined" && Reflect.get) { _get = Reflect.get.bind(); } else { _get = function _get(target, property, receiver) { var base = _superPropBase(target, property); if (!base) return; var desc = Object.getOwnPropertyDescriptor(base, property); if (desc.get) { return desc.get.call(arguments.length < 3 ? target : receiver); } return desc.value; }; } return _get.apply(this, arguments); }
function _superPropBase(object, property) { while (!Object.prototype.hasOwnProperty.call(object, property)) { object = _getPrototypeOf(object); if (object === null) break; } return object; }
function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function"); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, writable: true, configurable: true } }); Object.defineProperty(subClass, "prototype", { writable: false }); if (superClass) _setPrototypeOf(subClass, superClass); }
function _createSuper(Derived) { var hasNativeReflectConstruct = _isNativeReflectConstruct(); return function _createSuperInternal() { var Super = _getPrototypeOf(Derived), result; if (hasNativeReflectConstruct) { var NewTarget = _getPrototypeOf(this).constructor; result = Reflect.construct(Super, arguments, NewTarget); } else { result = Super.apply(this, arguments); } return _possibleConstructorReturn(this, result); }; }
function _possibleConstructorReturn(self, call) { if (call && (_typeof(call) === "object" || typeof call === "function")) { return call; } else if (call !== void 0) { throw new TypeError("Derived constructors may only return object or undefined"); } return _assertThisInitialized(self); }
function _assertThisInitialized(self) { if (self === void 0) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return self; }
function _wrapNativeSuper(Class) { var _cache = typeof Map === "function" ? new Map() : undefined; _wrapNativeSuper = function _wrapNativeSuper(Class) { if (Class === null || !_isNativeFunction(Class)) return Class; if (typeof Class !== "function") { throw new TypeError("Super expression must either be null or a function"); } if (typeof _cache !== "undefined") { if (_cache.has(Class)) return _cache.get(Class); _cache.set(Class, Wrapper); } function Wrapper() { return _construct(Class, arguments, _getPrototypeOf(this).constructor); } Wrapper.prototype = Object.create(Class.prototype, { constructor: { value: Wrapper, enumerable: false, writable: true, configurable: true } }); return _setPrototypeOf(Wrapper, Class); }; return _wrapNativeSuper(Class); }
function _construct(Parent, args, Class) { if (_isNativeReflectConstruct()) { _construct = Reflect.construct.bind(); } else { _construct = function _construct(Parent, args, Class) { var a = [null]; a.push.apply(a, args); var Constructor = Function.bind.apply(Parent, a); var instance = new Constructor(); if (Class) _setPrototypeOf(instance, Class.prototype); return instance; }; } return _construct.apply(null, arguments); }
function _isNativeReflectConstruct() { if (typeof Reflect === "undefined" || !Reflect.construct) return false; if (Reflect.construct.sham) return false; if (typeof Proxy === "function") return true; try { Boolean.prototype.valueOf.call(Reflect.construct(Boolean, [], function () {})); return true; } catch (e) { return false; } }
function _isNativeFunction(fn) { return Function.toString.call(fn).indexOf("[native code]") !== -1; }
function _setPrototypeOf(o, p) { _setPrototypeOf = Object.setPrototypeOf ? Object.setPrototypeOf.bind() : function _setPrototypeOf(o, p) { o.__proto__ = p; return o; }; return _setPrototypeOf(o, p); }
function _getPrototypeOf(o) { _getPrototypeOf = Object.setPrototypeOf ? Object.getPrototypeOf.bind() : function _getPrototypeOf(o) { return o.__proto__ || Object.getPrototypeOf(o); }; return _getPrototypeOf(o); }
function _toConsumableArray(arr) { return _arrayWithoutHoles(arr) || _iterableToArray(arr) || _unsupportedIterableToArray(arr) || _nonIterableSpread(); }
function _nonIterableSpread() { throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _iterableToArray(iter) { if (typeof Symbol !== "undefined" && iter[Symbol.iterator] != null || iter["@@iterator"] != null) return Array.from(iter); }
function _arrayWithoutHoles(arr) { if (Array.isArray(arr)) return _arrayLikeToArray(arr); }
function ownKeys(object, enumerableOnly) { var keys = Object.keys(object); if (Object.getOwnPropertySymbols) { var symbols = Object.getOwnPropertySymbols(object); enumerableOnly && (symbols = symbols.filter(function (sym) { return Object.getOwnPropertyDescriptor(object, sym).enumerable; })), keys.push.apply(keys, symbols); } return keys; }
function _objectSpread(target) { for (var i = 1; i < arguments.length; i++) { var source = null != arguments[i] ? arguments[i] : {}; i % 2 ? ownKeys(Object(source), !0).forEach(function (key) { _defineProperty(target, key, source[key]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(target, Object.getOwnPropertyDescriptors(source)) : ownKeys(Object(source)).forEach(function (key) { Object.defineProperty(target, key, Object.getOwnPropertyDescriptor(source, key)); }); } return target; }
function _defineProperty(obj, key, value) { key = _toPropertyKey(key); if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }
function _regeneratorRuntime() { "use strict"; /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/facebook/regenerator/blob/main/LICENSE */ _regeneratorRuntime = function _regeneratorRuntime() { return exports; }; var exports = {}, Op = Object.prototype, hasOwn = Op.hasOwnProperty, defineProperty = Object.defineProperty || function (obj, key, desc) { obj[key] = desc.value; }, $Symbol = "function" == typeof Symbol ? Symbol : {}, iteratorSymbol = $Symbol.iterator || "@@iterator", asyncIteratorSymbol = $Symbol.asyncIterator || "@@asyncIterator", toStringTagSymbol = $Symbol.toStringTag || "@@toStringTag"; function define(obj, key, value) { return Object.defineProperty(obj, key, { value: value, enumerable: !0, configurable: !0, writable: !0 }), obj[key]; } try { define({}, ""); } catch (err) { define = function define(obj, key, value) { return obj[key] = value; }; } function wrap(innerFn, outerFn, self, tryLocsList) { var protoGenerator = outerFn && outerFn.prototype instanceof Generator ? outerFn : Generator, generator = Object.create(protoGenerator.prototype), context = new Context(tryLocsList || []); return defineProperty(generator, "_invoke", { value: makeInvokeMethod(innerFn, self, context) }), generator; } function tryCatch(fn, obj, arg) { try { return { type: "normal", arg: fn.call(obj, arg) }; } catch (err) { return { type: "throw", arg: err }; } } exports.wrap = wrap; var ContinueSentinel = {}; function Generator() {} function GeneratorFunction() {} function GeneratorFunctionPrototype() {} var IteratorPrototype = {}; define(IteratorPrototype, iteratorSymbol, function () { return this; }); var getProto = Object.getPrototypeOf, NativeIteratorPrototype = getProto && getProto(getProto(values([]))); NativeIteratorPrototype && NativeIteratorPrototype !== Op && hasOwn.call(NativeIteratorPrototype, iteratorSymbol) && (IteratorPrototype = NativeIteratorPrototype); var Gp = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(IteratorPrototype); function defineIteratorMethods(prototype) { ["next", "throw", "return"].forEach(function (method) { define(prototype, method, function (arg) { return this._invoke(method, arg); }); }); } function AsyncIterator(generator, PromiseImpl) { function invoke(method, arg, resolve, reject) { var record = tryCatch(generator[method], generator, arg); if ("throw" !== record.type) { var result = record.arg, value = result.value; return value && "object" == _typeof(value) && hasOwn.call(value, "__await") ? PromiseImpl.resolve(value.__await).then(function (value) { invoke("next", value, resolve, reject); }, function (err) { invoke("throw", err, resolve, reject); }) : PromiseImpl.resolve(value).then(function (unwrapped) { result.value = unwrapped, resolve(result); }, function (error) { return invoke("throw", error, resolve, reject); }); } reject(record.arg); } var previousPromise; defineProperty(this, "_invoke", { value: function value(method, arg) { function callInvokeWithMethodAndArg() { return new PromiseImpl(function (resolve, reject) { invoke(method, arg, resolve, reject); }); } return previousPromise = previousPromise ? previousPromise.then(callInvokeWithMethodAndArg, callInvokeWithMethodAndArg) : callInvokeWithMethodAndArg(); } }); } function makeInvokeMethod(innerFn, self, context) { var state = "suspendedStart"; return function (method, arg) { if ("executing" === state) throw new Error("Generator is already running"); if ("completed" === state) { if ("throw" === method) throw arg; return doneResult(); } for (context.method = method, context.arg = arg;;) { var delegate = context.delegate; if (delegate) { var delegateResult = maybeInvokeDelegate(delegate, context); if (delegateResult) { if (delegateResult === ContinueSentinel) continue; return delegateResult; } } if ("next" === context.method) context.sent = context._sent = context.arg;else if ("throw" === context.method) { if ("suspendedStart" === state) throw state = "completed", context.arg; context.dispatchException(context.arg); } else "return" === context.method && context.abrupt("return", context.arg); state = "executing"; var record = tryCatch(innerFn, self, context); if ("normal" === record.type) { if (state = context.done ? "completed" : "suspendedYield", record.arg === ContinueSentinel) continue; return { value: record.arg, done: context.done }; } "throw" === record.type && (state = "completed", context.method = "throw", context.arg = record.arg); } }; } function maybeInvokeDelegate(delegate, context) { var methodName = context.method, method = delegate.iterator[methodName]; if (undefined === method) return context.delegate = null, "throw" === methodName && delegate.iterator.return && (context.method = "return", context.arg = undefined, maybeInvokeDelegate(delegate, context), "throw" === context.method) || "return" !== methodName && (context.method = "throw", context.arg = new TypeError("The iterator does not provide a '" + methodName + "' method")), ContinueSentinel; var record = tryCatch(method, delegate.iterator, context.arg); if ("throw" === record.type) return context.method = "throw", context.arg = record.arg, context.delegate = null, ContinueSentinel; var info = record.arg; return info ? info.done ? (context[delegate.resultName] = info.value, context.next = delegate.nextLoc, "return" !== context.method && (context.method = "next", context.arg = undefined), context.delegate = null, ContinueSentinel) : info : (context.method = "throw", context.arg = new TypeError("iterator result is not an object"), context.delegate = null, ContinueSentinel); } function pushTryEntry(locs) { var entry = { tryLoc: locs[0] }; 1 in locs && (entry.catchLoc = locs[1]), 2 in locs && (entry.finallyLoc = locs[2], entry.afterLoc = locs[3]), this.tryEntries.push(entry); } function resetTryEntry(entry) { var record = entry.completion || {}; record.type = "normal", delete record.arg, entry.completion = record; } function Context(tryLocsList) { this.tryEntries = [{ tryLoc: "root" }], tryLocsList.forEach(pushTryEntry, this), this.reset(!0); } function values(iterable) { if (iterable) { var iteratorMethod = iterable[iteratorSymbol]; if (iteratorMethod) return iteratorMethod.call(iterable); if ("function" == typeof iterable.next) return iterable; if (!isNaN(iterable.length)) { var i = -1, next = function next() { for (; ++i < iterable.length;) if (hasOwn.call(iterable, i)) return next.value = iterable[i], next.done = !1, next; return next.value = undefined, next.done = !0, next; }; return next.next = next; } } return { next: doneResult }; } function doneResult() { return { value: undefined, done: !0 }; } return GeneratorFunction.prototype = GeneratorFunctionPrototype, defineProperty(Gp, "constructor", { value: GeneratorFunctionPrototype, configurable: !0 }), defineProperty(GeneratorFunctionPrototype, "constructor", { value: GeneratorFunction, configurable: !0 }), GeneratorFunction.displayName = define(GeneratorFunctionPrototype, toStringTagSymbol, "GeneratorFunction"), exports.isGeneratorFunction = function (genFun) { var ctor = "function" == typeof genFun && genFun.constructor; return !!ctor && (ctor === GeneratorFunction || "GeneratorFunction" === (ctor.displayName || ctor.name)); }, exports.mark = function (genFun) { return Object.setPrototypeOf ? Object.setPrototypeOf(genFun, GeneratorFunctionPrototype) : (genFun.__proto__ = GeneratorFunctionPrototype, define(genFun, toStringTagSymbol, "GeneratorFunction")), genFun.prototype = Object.create(Gp), genFun; }, exports.awrap = function (arg) { return { __await: arg }; }, defineIteratorMethods(AsyncIterator.prototype), define(AsyncIterator.prototype, asyncIteratorSymbol, function () { return this; }), exports.AsyncIterator = AsyncIterator, exports.async = function (innerFn, outerFn, self, tryLocsList, PromiseImpl) { void 0 === PromiseImpl && (PromiseImpl = Promise); var iter = new AsyncIterator(wrap(innerFn, outerFn, self, tryLocsList), PromiseImpl); return exports.isGeneratorFunction(outerFn) ? iter : iter.next().then(function (result) { return result.done ? result.value : iter.next(); }); }, defineIteratorMethods(Gp), define(Gp, toStringTagSymbol, "Generator"), define(Gp, iteratorSymbol, function () { return this; }), define(Gp, "toString", function () { return "[object Generator]"; }), exports.keys = function (val) { var object = Object(val), keys = []; for (var key in object) keys.push(key); return keys.reverse(), function next() { for (; keys.length;) { var key = keys.pop(); if (key in object) return next.value = key, next.done = !1, next; } return next.done = !0, next; }; }, exports.values = values, Context.prototype = { constructor: Context, reset: function reset(skipTempReset) { if (this.prev = 0, this.next = 0, this.sent = this._sent = undefined, this.done = !1, this.delegate = null, this.method = "next", this.arg = undefined, this.tryEntries.forEach(resetTryEntry), !skipTempReset) for (var name in this) "t" === name.charAt(0) && hasOwn.call(this, name) && !isNaN(+name.slice(1)) && (this[name] = undefined); }, stop: function stop() { this.done = !0; var rootRecord = this.tryEntries[0].completion; if ("throw" === rootRecord.type) throw rootRecord.arg; return this.rval; }, dispatchException: function dispatchException(exception) { if (this.done) throw exception; var context = this; function handle(loc, caught) { return record.type = "throw", record.arg = exception, context.next = loc, caught && (context.method = "next", context.arg = undefined), !!caught; } for (var i = this.tryEntries.length - 1; i >= 0; --i) { var entry = this.tryEntries[i], record = entry.completion; if ("root" === entry.tryLoc) return handle("end"); if (entry.tryLoc <= this.prev) { var hasCatch = hasOwn.call(entry, "catchLoc"), hasFinally = hasOwn.call(entry, "finallyLoc"); if (hasCatch && hasFinally) { if (this.prev < entry.catchLoc) return handle(entry.catchLoc, !0); if (this.prev < entry.finallyLoc) return handle(entry.finallyLoc); } else if (hasCatch) { if (this.prev < entry.catchLoc) return handle(entry.catchLoc, !0); } else { if (!hasFinally) throw new Error("try statement without catch or finally"); if (this.prev < entry.finallyLoc) return handle(entry.finallyLoc); } } } }, abrupt: function abrupt(type, arg) { for (var i = this.tryEntries.length - 1; i >= 0; --i) { var entry = this.tryEntries[i]; if (entry.tryLoc <= this.prev && hasOwn.call(entry, "finallyLoc") && this.prev < entry.finallyLoc) { var finallyEntry = entry; break; } } finallyEntry && ("break" === type || "continue" === type) && finallyEntry.tryLoc <= arg && arg <= finallyEntry.finallyLoc && (finallyEntry = null); var record = finallyEntry ? finallyEntry.completion : {}; return record.type = type, record.arg = arg, finallyEntry ? (this.method = "next", this.next = finallyEntry.finallyLoc, ContinueSentinel) : this.complete(record); }, complete: function complete(record, afterLoc) { if ("throw" === record.type) throw record.arg; return "break" === record.type || "continue" === record.type ? this.next = record.arg : "return" === record.type ? (this.rval = this.arg = record.arg, this.method = "return", this.next = "end") : "normal" === record.type && afterLoc && (this.next = afterLoc), ContinueSentinel; }, finish: function finish(finallyLoc) { for (var i = this.tryEntries.length - 1; i >= 0; --i) { var entry = this.tryEntries[i]; if (entry.finallyLoc === finallyLoc) return this.complete(entry.completion, entry.afterLoc), resetTryEntry(entry), ContinueSentinel; } }, catch: function _catch(tryLoc) { for (var i = this.tryEntries.length - 1; i >= 0; --i) { var entry = this.tryEntries[i]; if (entry.tryLoc === tryLoc) { var record = entry.completion; if ("throw" === record.type) { var thrown = record.arg; resetTryEntry(entry); } return thrown; } } throw new Error("illegal catch attempt"); }, delegateYield: function delegateYield(iterable, resultName, nextLoc) { return this.delegate = { iterator: values(iterable), resultName: resultName, nextLoc: nextLoc }, "next" === this.method && (this.arg = undefined), ContinueSentinel; } }, exports; }
function asyncGeneratorStep(gen, resolve, reject, _next, _throw, key, arg) { try { var info = gen[key](arg); var value = info.value; } catch (error) { reject(error); return; } if (info.done) { resolve(value); } else { Promise.resolve(value).then(_next, _throw); } }
function _asyncToGenerator(fn) { return function () { var self = this, args = arguments; return new Promise(function (resolve, reject) { var gen = fn.apply(self, args); function _next(value) { asyncGeneratorStep(gen, resolve, reject, _next, _throw, "next", value); } function _throw(err) { asyncGeneratorStep(gen, resolve, reject, _next, _throw, "throw", err); } _next(undefined); }); }; }
function _slicedToArray(arr, i) { return _arrayWithHoles(arr) || _iterableToArrayLimit(arr, i) || _unsupportedIterableToArray(arr, i) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }
function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) arr2[i] = arr[i]; return arr2; }
function _iterableToArrayLimit(arr, i) { var _i = null == arr ? null : "undefined" != typeof Symbol && arr[Symbol.iterator] || arr["@@iterator"]; if (null != _i) { var _s, _e, _x, _r, _arr = [], _n = !0, _d = !1; try { if (_x = (_i = _i.call(arr)).next, 0 === i) { if (Object(_i) !== _i) return; _n = !1; } else for (; !(_n = (_s = _x.call(_i)).done) && (_arr.push(_s.value), _arr.length !== i); _n = !0); } catch (err) { _d = !0, _e = err; } finally { try { if (!_n && null != _i.return && (_r = _i.return(), Object(_r) !== _r)) return; } finally { if (_d) throw _e; } } return _arr; } }
function _arrayWithHoles(arr) { if (Array.isArray(arr)) return arr; }
function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }
function _defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, _toPropertyKey(descriptor.key), descriptor); } }
function _createClass(Constructor, protoProps, staticProps) { if (protoProps) _defineProperties(Constructor.prototype, protoProps); if (staticProps) _defineProperties(Constructor, staticProps); Object.defineProperty(Constructor, "prototype", { writable: false }); return Constructor; }
function _toPropertyKey(arg) { var key = _toPrimitive(arg, "string"); return _typeof(key) === "symbol" ? key : String(key); }
function _toPrimitive(input, hint) { if (_typeof(input) !== "object" || input === null) return input; var prim = input[Symbol.toPrimitive]; if (prim !== undefined) { var res = prim.call(input, hint || "default"); if (_typeof(res) !== "object") return res; throw new TypeError("@@toPrimitive must return a primitive value."); } return (hint === "string" ? String : Number)(input); }
function _typeof(obj) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (obj) { return typeof obj; } : function (obj) { return obj && "function" == typeof Symbol && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; }, _typeof(obj); }
var Pt = Object.defineProperty;
var Nt = function Nt(e, t, r) {
  return t in e ? Pt(e, t, {
    enumerable: !0,
    configurable: !0,
    writable: !0,
    value: r
  }) : e[t] = r;
};
var me = function me(e, t, r) {
  return Nt(e, _typeof(t) != "symbol" ? t + "" : t, r), r;
};
import { b as U, ai as Xe, aj as Te, ak as Ze, al as kt } from "./__uno-bcdf16b1.js";
import { k as Qe } from "./url-68a935bf.js";
function Ye(e, t) {
  return function () {
    return e.apply(t, arguments);
  };
}
var _t = Object.prototype.toString,
  Ce = Object.getPrototypeOf,
  se = function (e) {
    return function (t) {
      var r = _t.call(t);
      return e[r] || (e[r] = r.slice(8, -1).toLowerCase());
    };
  }(Object.create(null)),
  j = function j(e) {
    return e = e.toLowerCase(), function (t) {
      return se(t) === e;
    };
  },
  oe = function oe(e) {
    return function (t) {
      return _typeof(t) === e;
    };
  },
  J = Array.isArray,
  V = oe("undefined");
function Mt(e) {
  return e !== null && !V(e) && e.constructor !== null && !V(e.constructor) && M(e.constructor.isBuffer) && e.constructor.isBuffer(e);
}
var et = j("ArrayBuffer");
function vt(e) {
  var t;
  return (typeof ArrayBuffer === "undefined" ? "undefined" : _typeof(ArrayBuffer)) < "u" && ArrayBuffer.isView ? t = ArrayBuffer.isView(e) : t = e && e.buffer && et(e.buffer), t;
}
var It = oe("string"),
  M = oe("function"),
  tt = oe("number"),
  ie = function ie(e) {
    return e !== null && _typeof(e) == "object";
  },
  Ft = function Ft(e) {
    return e === !0 || e === !1;
  },
  Z = function Z(e) {
    if (se(e) !== "object") return !1;
    var t = Ce(e);
    return (t === null || t === Object.prototype || Object.getPrototypeOf(t) === null) && !(Symbol.toStringTag in e) && !(Symbol.iterator in e);
  },
  Dt = j("Date"),
  jt = j("File"),
  Bt = j("Blob"),
  Lt = j("FileList"),
  Ut = function Ut(e) {
    return ie(e) && M(e.pipe);
  },
  qt = function qt(e) {
    var t;
    return e && (typeof FormData == "function" && e instanceof FormData || M(e.append) && ((t = se(e)) === "formdata" || t === "object" && M(e.toString) && e.toString() === "[object FormData]"));
  },
  $t = j("URLSearchParams"),
  Ht = function Ht(e) {
    return e.trim ? e.trim() : e.replace(/^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g, "");
  };
function K(e, t) {
  var _ref = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : {},
    _ref$allOwnKeys = _ref.allOwnKeys,
    r = _ref$allOwnKeys === void 0 ? !1 : _ref$allOwnKeys;
  if (e === null || _typeof(e) > "u") return;
  var n, s;
  if (_typeof(e) != "object" && (e = [e]), J(e)) for (n = 0, s = e.length; n < s; n++) t.call(null, e[n], n, e);else {
    var i = r ? Object.getOwnPropertyNames(e) : Object.keys(e),
      o = i.length;
    var a;
    for (n = 0; n < o; n++) a = i[n], t.call(null, e[a], a, e);
  }
}
function rt(e, t) {
  t = t.toLowerCase();
  var r = Object.keys(e);
  var n = r.length,
    s;
  for (; n-- > 0;) if (s = r[n], t === s.toLowerCase()) return s;
  return null;
}
var nt = function () {
    return (typeof globalThis === "undefined" ? "undefined" : _typeof(globalThis)) < "u" ? globalThis : (typeof self === "undefined" ? "undefined" : _typeof(self)) < "u" ? self : (typeof window === "undefined" ? "undefined" : _typeof(window)) < "u" ? window : global;
  }(),
  st = function st(e) {
    return !V(e) && e !== nt;
  };
function be() {
  var _ref2 = st(this) && this || {},
    e = _ref2.caseless,
    t = {},
    r = function r(n, s) {
      var i = e && rt(t, s) || s;
      Z(t[i]) && Z(n) ? t[i] = be(t[i], n) : Z(n) ? t[i] = be({}, n) : J(n) ? t[i] = n.slice() : t[i] = n;
    };
  for (var n = 0, s = arguments.length; n < s; n++) arguments[n] && K(arguments[n], r);
  return t;
}
var Jt = function Jt(e, t, r) {
    var _ref3 = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : {},
      n = _ref3.allOwnKeys;
    return K(t, function (s, i) {
      r && M(s) ? e[i] = Ye(s, r) : e[i] = s;
    }, {
      allOwnKeys: n
    }), e;
  },
  zt = function zt(e) {
    return e.charCodeAt(0) === 65279 && (e = e.slice(1)), e;
  },
  Wt = function Wt(e, t, r, n) {
    e.prototype = Object.create(t.prototype, n), e.prototype.constructor = e, Object.defineProperty(e, "super", {
      value: t.prototype
    }), r && Object.assign(e.prototype, r);
  },
  Vt = function Vt(e, t, r, n) {
    var s, i, o;
    var a = {};
    if (t = t || {}, e == null) return t;
    do {
      for (s = Object.getOwnPropertyNames(e), i = s.length; i-- > 0;) o = s[i], (!n || n(o, e, t)) && !a[o] && (t[o] = e[o], a[o] = !0);
      e = r !== !1 && Ce(e);
    } while (e && (!r || r(e, t)) && e !== Object.prototype);
    return t;
  },
  Kt = function Kt(e, t, r) {
    e = String(e), (r === void 0 || r > e.length) && (r = e.length), r -= t.length;
    var n = e.indexOf(t, r);
    return n !== -1 && n === r;
  },
  Gt = function Gt(e) {
    if (!e) return null;
    if (J(e)) return e;
    var t = e.length;
    if (!tt(t)) return null;
    var r = new Array(t);
    for (; t-- > 0;) r[t] = e[t];
    return r;
  },
  Xt = function (e) {
    return function (t) {
      return e && t instanceof e;
    };
  }((typeof Uint8Array === "undefined" ? "undefined" : _typeof(Uint8Array)) < "u" && Ce(Uint8Array)),
  Zt = function Zt(e, t) {
    var n = (e && e[Symbol.iterator]).call(e);
    var s;
    for (; (s = n.next()) && !s.done;) {
      var i = s.value;
      t.call(e, i[0], i[1]);
    }
  },
  Qt = function Qt(e, t) {
    var r;
    var n = [];
    for (; (r = e.exec(t)) !== null;) n.push(r);
    return n;
  },
  Yt = j("HTMLFormElement"),
  er = function er(e) {
    return e.toLowerCase().replace(/[-_\s]([a-z\d])(\w*)/g, function (r, n, s) {
      return n.toUpperCase() + s;
    });
  },
  De = function (_ref4) {
    var e = _ref4.hasOwnProperty;
    return function (t, r) {
      return e.call(t, r);
    };
  }(Object.prototype),
  tr = j("RegExp"),
  ot = function ot(e, t) {
    var r = Object.getOwnPropertyDescriptors(e),
      n = {};
    K(r, function (s, i) {
      t(s, i, e) !== !1 && (n[i] = s);
    }), Object.defineProperties(e, n);
  },
  rr = function rr(e) {
    ot(e, function (t, r) {
      if (M(e) && ["arguments", "caller", "callee"].indexOf(r) !== -1) return !1;
      var n = e[r];
      if (M(n)) {
        if (t.enumerable = !1, "writable" in t) {
          t.writable = !1;
          return;
        }
        t.set || (t.set = function () {
          throw Error("Can not rewrite read-only method '" + r + "'");
        });
      }
    });
  },
  nr = function nr(e, t) {
    var r = {},
      n = function n(s) {
        s.forEach(function (i) {
          r[i] = !0;
        });
      };
    return J(e) ? n(e) : n(String(e).split(t)), r;
  },
  sr = function sr() {},
  or = function or(e, t) {
    return e = +e, Number.isFinite(e) ? e : t;
  },
  ge = "abcdefghijklmnopqrstuvwxyz",
  je = "0123456789",
  it = {
    DIGIT: je,
    ALPHA: ge,
    ALPHA_DIGIT: ge + ge.toUpperCase() + je
  },
  ir = function ir() {
    var e = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : 16;
    var t = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : it.ALPHA_DIGIT;
    var r = "";
    var n = t.length;
    for (; e--;) r += t[Math.random() * n | 0];
    return r;
  };
function ar(e) {
  return !!(e && M(e.append) && e[Symbol.toStringTag] === "FormData" && e[Symbol.iterator]);
}
var cr = function cr(e) {
    var t = new Array(10),
      r = function r(n, s) {
        if (ie(n)) {
          if (t.indexOf(n) >= 0) return;
          if (!("toJSON" in n)) {
            t[s] = n;
            var i = J(n) ? [] : {};
            return K(n, function (o, a) {
              var u = r(o, s + 1);
              !V(u) && (i[a] = u);
            }), t[s] = void 0, i;
          }
        }
        return n;
      };
    return r(e, 0);
  },
  lr = j("AsyncFunction"),
  ur = function ur(e) {
    return e && (ie(e) || M(e)) && M(e.then) && M(e.catch);
  },
  l = {
    isArray: J,
    isArrayBuffer: et,
    isBuffer: Mt,
    isFormData: qt,
    isArrayBufferView: vt,
    isString: It,
    isNumber: tt,
    isBoolean: Ft,
    isObject: ie,
    isPlainObject: Z,
    isUndefined: V,
    isDate: Dt,
    isFile: jt,
    isBlob: Bt,
    isRegExp: tr,
    isFunction: M,
    isStream: Ut,
    isURLSearchParams: $t,
    isTypedArray: Xt,
    isFileList: Lt,
    forEach: K,
    merge: be,
    extend: Jt,
    trim: Ht,
    stripBOM: zt,
    inherits: Wt,
    toFlatObject: Vt,
    kindOf: se,
    kindOfTest: j,
    endsWith: Kt,
    toArray: Gt,
    forEachEntry: Zt,
    matchAll: Qt,
    isHTMLForm: Yt,
    hasOwnProperty: De,
    hasOwnProp: De,
    reduceDescriptors: ot,
    freezeMethods: rr,
    toObjectSet: nr,
    toCamelCase: er,
    noop: sr,
    toFiniteNumber: or,
    findKey: rt,
    global: nt,
    isContextDefined: st,
    ALPHABET: it,
    generateString: ir,
    isSpecCompliantForm: ar,
    toJSONObject: cr,
    isAsyncFn: lr,
    isThenable: ur
  };
function b(e, t, r, n, s) {
  Error.call(this), Error.captureStackTrace ? Error.captureStackTrace(this, this.constructor) : this.stack = new Error().stack, this.message = e, this.name = "AxiosError", t && (this.code = t), r && (this.config = r), n && (this.request = n), s && (this.response = s);
}
l.inherits(b, Error, {
  toJSON: function toJSON() {
    return {
      message: this.message,
      name: this.name,
      description: this.description,
      number: this.number,
      fileName: this.fileName,
      lineNumber: this.lineNumber,
      columnNumber: this.columnNumber,
      stack: this.stack,
      config: l.toJSONObject(this.config),
      code: this.code,
      status: this.response && this.response.status ? this.response.status : null
    };
  }
});
var at = b.prototype,
  ct = {};
["ERR_BAD_OPTION_VALUE", "ERR_BAD_OPTION", "ECONNABORTED", "ETIMEDOUT", "ERR_NETWORK", "ERR_FR_TOO_MANY_REDIRECTS", "ERR_DEPRECATED", "ERR_BAD_RESPONSE", "ERR_BAD_REQUEST", "ERR_CANCELED", "ERR_NOT_SUPPORT", "ERR_INVALID_URL"].forEach(function (e) {
  ct[e] = {
    value: e
  };
});
Object.defineProperties(b, ct);
Object.defineProperty(at, "isAxiosError", {
  value: !0
});
b.from = function (e, t, r, n, s, i) {
  var o = Object.create(at);
  return l.toFlatObject(e, o, function (u) {
    return u !== Error.prototype;
  }, function (a) {
    return a !== "isAxiosError";
  }), b.call(o, e.message, t, r, n, s), o.cause = e, o.name = e.name, i && Object.assign(o, i), o;
};
var fr = null;
function xe(e) {
  return l.isPlainObject(e) || l.isArray(e);
}
function lt(e) {
  return l.endsWith(e, "[]") ? e.slice(0, -2) : e;
}
function Be(e, t, r) {
  return e ? e.concat(t).map(function (s, i) {
    return s = lt(s), !r && i ? "[" + s + "]" : s;
  }).join(r ? "." : "") : t;
}
function dr(e) {
  return l.isArray(e) && !e.some(xe);
}
var mr = l.toFlatObject(l, {}, null, function (t) {
  return /^is[A-Z]/.test(t);
});
function ae(e, t, r) {
  if (!l.isObject(e)) throw new TypeError("target must be an object");
  t = t || new FormData(), r = l.toFlatObject(r, {
    metaTokens: !0,
    dots: !1,
    indexes: !1
  }, !1, function (h, S) {
    return !l.isUndefined(S[h]);
  });
  var n = r.metaTokens,
    s = r.visitor || f,
    i = r.dots,
    o = r.indexes,
    u = (r.Blob || (typeof Blob === "undefined" ? "undefined" : _typeof(Blob)) < "u" && Blob) && l.isSpecCompliantForm(t);
  if (!l.isFunction(s)) throw new TypeError("visitor must be a function");
  function c(d) {
    if (d === null) return "";
    if (l.isDate(d)) return d.toISOString();
    if (!u && l.isBlob(d)) throw new b("Blob is not supported. Use a Buffer instead.");
    return l.isArrayBuffer(d) || l.isTypedArray(d) ? u && typeof Blob == "function" ? new Blob([d]) : Buffer.from(d) : d;
  }
  function f(d, h, S) {
    var C = d;
    if (d && !S && _typeof(d) == "object") {
      if (l.endsWith(h, "{}")) h = n ? h : h.slice(0, -2), d = JSON.stringify(d);else if (l.isArray(d) && dr(d) || (l.isFileList(d) || l.endsWith(h, "[]")) && (C = l.toArray(d))) return h = lt(h), C.forEach(function (I, ue) {
        !(l.isUndefined(I) || I === null) && t.append(o === !0 ? Be([h], ue, i) : o === null ? h : h + "[]", c(I));
      }), !1;
    }
    return xe(d) ? !0 : (t.append(Be(S, h, i), c(d)), !1);
  }
  var m = [],
    y = Object.assign(mr, {
      defaultVisitor: f,
      convertValue: c,
      isVisitable: xe
    });
  function A(d, h) {
    if (!l.isUndefined(d)) {
      if (m.indexOf(d) !== -1) throw Error("Circular reference detected in " + h.join("."));
      m.push(d), l.forEach(d, function (C, N) {
        (!(l.isUndefined(C) || C === null) && s.call(t, C, l.isString(N) ? N.trim() : N, h, y)) === !0 && A(C, h ? h.concat(N) : [N]);
      }), m.pop();
    }
  }
  if (!l.isObject(e)) throw new TypeError("data must be an object");
  return A(e), t;
}
function Le(e) {
  var t = {
    "!": "%21",
    "'": "%27",
    "(": "%28",
    ")": "%29",
    "~": "%7E",
    "%20": "+",
    "%00": "\0"
  };
  return encodeURIComponent(e).replace(/[!'()~]|%20|%00/g, function (n) {
    return t[n];
  });
}
function Pe(e, t) {
  this._pairs = [], e && ae(e, this, t);
}
var ut = Pe.prototype;
ut.append = function (t, r) {
  this._pairs.push([t, r]);
};
ut.toString = function (t) {
  var r = t ? function (n) {
    return t.call(this, n, Le);
  } : Le;
  return this._pairs.map(function (s) {
    return r(s[0]) + "=" + r(s[1]);
  }, "").join("&");
};
function gr(e) {
  return encodeURIComponent(e).replace(/%3A/gi, ":").replace(/%24/g, "$").replace(/%2C/gi, ",").replace(/%20/g, "+").replace(/%5B/gi, "[").replace(/%5D/gi, "]");
}
function ft(e, t, r) {
  if (!t) return e;
  var n = r && r.encode || gr,
    s = r && r.serialize;
  var i;
  if (s ? i = s(t, r) : i = l.isURLSearchParams(t) ? t.toString() : new Pe(t, r).toString(n), i) {
    var o = e.indexOf("#");
    o !== -1 && (e = e.slice(0, o)), e += (e.indexOf("?") === -1 ? "?" : "&") + i;
  }
  return e;
}
var pr = /*#__PURE__*/function () {
  function pr() {
    _classCallCheck(this, pr);
    this.handlers = [];
  }
  _createClass(pr, [{
    key: "use",
    value: function use(t, r, n) {
      return this.handlers.push({
        fulfilled: t,
        rejected: r,
        synchronous: n ? n.synchronous : !1,
        runWhen: n ? n.runWhen : null
      }), this.handlers.length - 1;
    }
  }, {
    key: "eject",
    value: function eject(t) {
      this.handlers[t] && (this.handlers[t] = null);
    }
  }, {
    key: "clear",
    value: function clear() {
      this.handlers && (this.handlers = []);
    }
  }, {
    key: "forEach",
    value: function forEach(t) {
      l.forEach(this.handlers, function (n) {
        n !== null && t(n);
      });
    }
  }]);
  return pr;
}();
var Ue = pr,
  dt = {
    silentJSONParsing: !0,
    forcedJSONParsing: !0,
    clarifyTimeoutError: !1
  },
  hr = (typeof URLSearchParams === "undefined" ? "undefined" : _typeof(URLSearchParams)) < "u" ? URLSearchParams : Pe,
  Ar = (typeof FormData === "undefined" ? "undefined" : _typeof(FormData)) < "u" ? FormData : null,
  yr = (typeof Blob === "undefined" ? "undefined" : _typeof(Blob)) < "u" ? Blob : null,
  wr = function () {
    var e;
    return (typeof navigator === "undefined" ? "undefined" : _typeof(navigator)) < "u" && ((e = navigator.product) === "ReactNative" || e === "NativeScript" || e === "NS") ? !1 : (typeof window === "undefined" ? "undefined" : _typeof(window)) < "u" && (typeof document === "undefined" ? "undefined" : _typeof(document)) < "u";
  }(),
  br = function () {
    return (typeof WorkerGlobalScope === "undefined" ? "undefined" : _typeof(WorkerGlobalScope)) < "u" && self instanceof WorkerGlobalScope && typeof self.importScripts == "function";
  }(),
  D = {
    isBrowser: !0,
    classes: {
      URLSearchParams: hr,
      FormData: Ar,
      Blob: yr
    },
    isStandardBrowserEnv: wr,
    isStandardBrowserWebWorkerEnv: br,
    protocols: ["http", "https", "file", "blob", "url", "data"]
  };
function xr(e, t) {
  return ae(e, new D.classes.URLSearchParams(), Object.assign({
    visitor: function visitor(r, n, s, i) {
      return D.isNode && l.isBuffer(r) ? (this.append(n, r.toString("base64")), !1) : i.defaultVisitor.apply(this, arguments);
    }
  }, t));
}
function Er(e) {
  return l.matchAll(/\w+|\[(\w*)]/g, e).map(function (t) {
    return t[0] === "[]" ? "" : t[1] || t[0];
  });
}
function Sr(e) {
  var t = {},
    r = Object.keys(e);
  var n;
  var s = r.length;
  var i;
  for (n = 0; n < s; n++) i = r[n], t[i] = e[i];
  return t;
}
function mt(e) {
  function t(r, n, s, i) {
    var o = r[i++];
    var a = Number.isFinite(+o),
      u = i >= r.length;
    return o = !o && l.isArray(s) ? s.length : o, u ? (l.hasOwnProp(s, o) ? s[o] = [s[o], n] : s[o] = n, !a) : ((!s[o] || !l.isObject(s[o])) && (s[o] = []), t(r, n, s[o], i) && l.isArray(s[o]) && (s[o] = Sr(s[o])), !a);
  }
  if (l.isFormData(e) && l.isFunction(e.entries)) {
    var r = {};
    return l.forEachEntry(e, function (n, s) {
      t(Er(n), s, r, 0);
    }), r;
  }
  return null;
}
var Or = {
  "Content-Type": void 0
};
function Rr(e, t, r) {
  if (l.isString(e)) try {
    return (t || JSON.parse)(e), l.trim(e);
  } catch (n) {
    if (n.name !== "SyntaxError") throw n;
  }
  return (r || JSON.stringify)(e);
}
var ce = {
  transitional: dt,
  adapter: ["xhr", "http"],
  transformRequest: [function (t, r) {
    var n = r.getContentType() || "",
      s = n.indexOf("application/json") > -1,
      i = l.isObject(t);
    if (i && l.isHTMLForm(t) && (t = new FormData(t)), l.isFormData(t)) return s && s ? JSON.stringify(mt(t)) : t;
    if (l.isArrayBuffer(t) || l.isBuffer(t) || l.isStream(t) || l.isFile(t) || l.isBlob(t)) return t;
    if (l.isArrayBufferView(t)) return t.buffer;
    if (l.isURLSearchParams(t)) return r.setContentType("application/x-www-form-urlencoded;charset=utf-8", !1), t.toString();
    var a;
    if (i) {
      if (n.indexOf("application/x-www-form-urlencoded") > -1) return xr(t, this.formSerializer).toString();
      if ((a = l.isFileList(t)) || n.indexOf("multipart/form-data") > -1) {
        var u = this.env && this.env.FormData;
        return ae(a ? {
          "files[]": t
        } : t, u && new u(), this.formSerializer);
      }
    }
    return i || s ? (r.setContentType("application/json", !1), Rr(t)) : t;
  }],
  transformResponse: [function (t) {
    var r = this.transitional || ce.transitional,
      n = r && r.forcedJSONParsing,
      s = this.responseType === "json";
    if (t && l.isString(t) && (n && !this.responseType || s)) {
      var o = !(r && r.silentJSONParsing) && s;
      try {
        return JSON.parse(t);
      } catch (a) {
        if (o) throw a.name === "SyntaxError" ? b.from(a, b.ERR_BAD_RESPONSE, this, null, this.response) : a;
      }
    }
    return t;
  }],
  timeout: 0,
  xsrfCookieName: "XSRF-TOKEN",
  xsrfHeaderName: "X-XSRF-TOKEN",
  maxContentLength: -1,
  maxBodyLength: -1,
  env: {
    FormData: D.classes.FormData,
    Blob: D.classes.Blob
  },
  validateStatus: function validateStatus(t) {
    return t >= 200 && t < 300;
  },
  headers: {
    common: {
      Accept: "application/json, text/plain, */*"
    }
  }
};
l.forEach(["delete", "get", "head"], function (t) {
  ce.headers[t] = {};
});
l.forEach(["post", "put", "patch"], function (t) {
  ce.headers[t] = l.merge(Or);
});
var Ne = ce,
  Tr = l.toObjectSet(["age", "authorization", "content-length", "content-type", "etag", "expires", "from", "host", "if-modified-since", "if-unmodified-since", "last-modified", "location", "max-forwards", "proxy-authorization", "referer", "retry-after", "user-agent"]),
  Cr = function Cr(e) {
    var t = {};
    var r, n, s;
    return e && e.split("\n").forEach(function (o) {
      s = o.indexOf(":"), r = o.substring(0, s).trim().toLowerCase(), n = o.substring(s + 1).trim(), !(!r || t[r] && Tr[r]) && (r === "set-cookie" ? t[r] ? t[r].push(n) : t[r] = [n] : t[r] = t[r] ? t[r] + ", " + n : n);
    }), t;
  },
  qe = Symbol("internals");
function W(e) {
  return e && String(e).trim().toLowerCase();
}
function Q(e) {
  return e === !1 || e == null ? e : l.isArray(e) ? e.map(Q) : String(e);
}
function Pr(e) {
  var t = Object.create(null),
    r = /([^\s,;=]+)\s*(?:=\s*([^,;]+))?/g;
  var n;
  for (; n = r.exec(e);) t[n[1]] = n[2];
  return t;
}
var Nr = function Nr(e) {
  return /^[-_a-zA-Z0-9^`|~,!#$%&'*+.]+$/.test(e.trim());
};
function pe(e, t, r, n, s) {
  if (l.isFunction(n)) return n.call(this, t, r);
  if (s && (t = r), !!l.isString(t)) {
    if (l.isString(n)) return t.indexOf(n) !== -1;
    if (l.isRegExp(n)) return n.test(t);
  }
}
function kr(e) {
  return e.trim().toLowerCase().replace(/([a-z\d])(\w*)/g, function (t, r, n) {
    return r.toUpperCase() + n;
  });
}
function _r(e, t) {
  var r = l.toCamelCase(" " + t);
  ["get", "set", "has"].forEach(function (n) {
    Object.defineProperty(e, n + r, {
      value: function value(s, i, o) {
        return this[n].call(this, t, s, i, o);
      },
      configurable: !0
    });
  });
}
var le = /*#__PURE__*/function (_Symbol$iterator, _Symbol$toStringTag) {
  function le(t) {
    _classCallCheck(this, le);
    t && this.set(t);
  }
  _createClass(le, [{
    key: "set",
    value: function set(t, r, n) {
      var s = this;
      function i(a, u, c) {
        var f = W(u);
        if (!f) throw new Error("header name must be a non-empty string");
        var m = l.findKey(s, f);
        (!m || s[m] === void 0 || c === !0 || c === void 0 && s[m] !== !1) && (s[m || u] = Q(a));
      }
      var o = function o(a, u) {
        return l.forEach(a, function (c, f) {
          return i(c, f, u);
        });
      };
      return l.isPlainObject(t) || t instanceof this.constructor ? o(t, r) : l.isString(t) && (t = t.trim()) && !Nr(t) ? o(Cr(t), r) : t != null && i(r, t, n), this;
    }
  }, {
    key: "get",
    value: function get(t, r) {
      if (t = W(t), t) {
        var n = l.findKey(this, t);
        if (n) {
          var s = this[n];
          if (!r) return s;
          if (r === !0) return Pr(s);
          if (l.isFunction(r)) return r.call(this, s, n);
          if (l.isRegExp(r)) return r.exec(s);
          throw new TypeError("parser must be boolean|regexp|function");
        }
      }
    }
  }, {
    key: "has",
    value: function has(t, r) {
      if (t = W(t), t) {
        var n = l.findKey(this, t);
        return !!(n && this[n] !== void 0 && (!r || pe(this, this[n], n, r)));
      }
      return !1;
    }
  }, {
    key: "delete",
    value: function _delete(t, r) {
      var n = this;
      var s = !1;
      function i(o) {
        if (o = W(o), o) {
          var a = l.findKey(n, o);
          a && (!r || pe(n, n[a], a, r)) && (delete n[a], s = !0);
        }
      }
      return l.isArray(t) ? t.forEach(i) : i(t), s;
    }
  }, {
    key: "clear",
    value: function clear(t) {
      var r = Object.keys(this);
      var n = r.length,
        s = !1;
      for (; n--;) {
        var i = r[n];
        (!t || pe(this, this[i], i, t, !0)) && (delete this[i], s = !0);
      }
      return s;
    }
  }, {
    key: "normalize",
    value: function normalize(t) {
      var r = this,
        n = {};
      return l.forEach(this, function (s, i) {
        var o = l.findKey(n, i);
        if (o) {
          r[o] = Q(s), delete r[i];
          return;
        }
        var a = t ? kr(i) : String(i).trim();
        a !== i && delete r[i], r[a] = Q(s), n[a] = !0;
      }), this;
    }
  }, {
    key: "concat",
    value: function concat() {
      var _this$constructor;
      for (var _len = arguments.length, t = new Array(_len), _key = 0; _key < _len; _key++) {
        t[_key] = arguments[_key];
      }
      return (_this$constructor = this.constructor).concat.apply(_this$constructor, [this].concat(t));
    }
  }, {
    key: "toJSON",
    value: function toJSON(t) {
      var r = Object.create(null);
      return l.forEach(this, function (n, s) {
        n != null && n !== !1 && (r[s] = t && l.isArray(n) ? n.join(", ") : n);
      }), r;
    }
  }, {
    key: _Symbol$iterator,
    value: function value() {
      return Object.entries(this.toJSON())[Symbol.iterator]();
    }
  }, {
    key: "toString",
    value: function toString() {
      return Object.entries(this.toJSON()).map(function (_ref5) {
        var _ref6 = _slicedToArray(_ref5, 2),
          t = _ref6[0],
          r = _ref6[1];
        return t + ": " + r;
      }).join("\n");
    }
  }, {
    key: _Symbol$toStringTag,
    get: function get() {
      return "AxiosHeaders";
    }
  }], [{
    key: "from",
    value: function from(t) {
      return t instanceof this ? t : new this(t);
    }
  }, {
    key: "concat",
    value: function concat(t) {
      var n = new this(t);
      for (var _len2 = arguments.length, r = new Array(_len2 > 1 ? _len2 - 1 : 0), _key2 = 1; _key2 < _len2; _key2++) {
        r[_key2 - 1] = arguments[_key2];
      }
      return r.forEach(function (s) {
        return n.set(s);
      }), n;
    }
  }, {
    key: "accessor",
    value: function accessor(t) {
      var n = (this[qe] = this[qe] = {
          accessors: {}
        }).accessors,
        s = this.prototype;
      function i(o) {
        var a = W(o);
        n[a] || (_r(s, o), n[a] = !0);
      }
      return l.isArray(t) ? t.forEach(i) : i(t), this;
    }
  }]);
  return le;
}(Symbol.iterator, Symbol.toStringTag);
le.accessor(["Content-Type", "Content-Length", "Accept", "Accept-Encoding", "User-Agent", "Authorization"]);
l.freezeMethods(le.prototype);
l.freezeMethods(le);
var B = le;
function he(e, t) {
  var r = this || Ne,
    n = t || r,
    s = B.from(n.headers);
  var i = n.data;
  return l.forEach(e, function (a) {
    i = a.call(r, i, s.normalize(), t ? t.status : void 0);
  }), s.normalize(), i;
}
function gt(e) {
  return !!(e && e.__CANCEL__);
}
function G(e, t, r) {
  b.call(this, e !== null && e !== void 0 ? e : "canceled", b.ERR_CANCELED, t, r), this.name = "CanceledError";
}
l.inherits(G, b, {
  __CANCEL__: !0
});
function Mr(e, t, r) {
  var n = r.config.validateStatus;
  !r.status || !n || n(r.status) ? e(r) : t(new b("Request failed with status code " + r.status, [b.ERR_BAD_REQUEST, b.ERR_BAD_RESPONSE][Math.floor(r.status / 100) - 4], r.config, r.request, r));
}
var vr = D.isStandardBrowserEnv ? function () {
  return {
    write: function write(r, n, s, i, o, a) {
      var u = [];
      u.push(r + "=" + encodeURIComponent(n)), l.isNumber(s) && u.push("expires=" + new Date(s).toGMTString()), l.isString(i) && u.push("path=" + i), l.isString(o) && u.push("domain=" + o), a === !0 && u.push("secure"), document.cookie = u.join("; ");
    },
    read: function read(r) {
      var n = document.cookie.match(new RegExp("(^|;\\s*)(" + r + ")=([^;]*)"));
      return n ? decodeURIComponent(n[3]) : null;
    },
    remove: function remove(r) {
      this.write(r, "", Date.now() - 864e5);
    }
  };
}() : function () {
  return {
    write: function write() {},
    read: function read() {
      return null;
    },
    remove: function remove() {}
  };
}();
function Ir(e) {
  return /^([a-z][a-z\d+\-.]*:)?\/\//i.test(e);
}
function Fr(e, t) {
  return t ? e.replace(/\/+$/, "") + "/" + t.replace(/^\/+/, "") : e;
}
function pt(e, t) {
  return e && !Ir(t) ? Fr(e, t) : t;
}
var Dr = D.isStandardBrowserEnv ? function () {
  var t = /(msie|trident)/i.test(navigator.userAgent),
    r = document.createElement("a");
  var n;
  function s(i) {
    var o = i;
    return t && (r.setAttribute("href", o), o = r.href), r.setAttribute("href", o), {
      href: r.href,
      protocol: r.protocol ? r.protocol.replace(/:$/, "") : "",
      host: r.host,
      search: r.search ? r.search.replace(/^\?/, "") : "",
      hash: r.hash ? r.hash.replace(/^#/, "") : "",
      hostname: r.hostname,
      port: r.port,
      pathname: r.pathname.charAt(0) === "/" ? r.pathname : "/" + r.pathname
    };
  }
  return n = s(window.location.href), function (o) {
    var a = l.isString(o) ? s(o) : o;
    return a.protocol === n.protocol && a.host === n.host;
  };
}() : function () {
  return function () {
    return !0;
  };
}();
function jr(e) {
  var t = /^([-+\w]{1,25})(:?\/\/|:)/.exec(e);
  return t && t[1] || "";
}
function Br(e, t) {
  e = e || 10;
  var r = new Array(e),
    n = new Array(e);
  var s = 0,
    i = 0,
    o;
  return t = t !== void 0 ? t : 1e3, function (u) {
    var c = Date.now(),
      f = n[i];
    o || (o = c), r[s] = u, n[s] = c;
    var m = i,
      y = 0;
    for (; m !== s;) y += r[m++], m = m % e;
    if (s = (s + 1) % e, s === i && (i = (i + 1) % e), c - o < t) return;
    var A = f && c - f;
    return A ? Math.round(y * 1e3 / A) : void 0;
  };
}
function $e(e, t) {
  var r = 0;
  var n = Br(50, 250);
  return function (s) {
    var i = s.loaded,
      o = s.lengthComputable ? s.total : void 0,
      a = i - r,
      u = n(a),
      c = i <= o;
    r = i;
    var f = {
      loaded: i,
      total: o,
      progress: o ? i / o : void 0,
      bytes: a,
      rate: u || void 0,
      estimated: u && o && c ? (o - i) / u : void 0,
      event: s
    };
    f[t ? "download" : "upload"] = !0, e(f);
  };
}
var Lr = (typeof XMLHttpRequest === "undefined" ? "undefined" : _typeof(XMLHttpRequest)) < "u",
  Ur = Lr && function (e) {
    return new Promise(function (r, n) {
      var s = e.data;
      var i = B.from(e.headers).normalize(),
        o = e.responseType;
      var a;
      function u() {
        e.cancelToken && e.cancelToken.unsubscribe(a), e.signal && e.signal.removeEventListener("abort", a);
      }
      l.isFormData(s) && (D.isStandardBrowserEnv || D.isStandardBrowserWebWorkerEnv ? i.setContentType(!1) : i.setContentType("multipart/form-data;", !1));
      var c = new XMLHttpRequest();
      if (e.auth) {
        var A = e.auth.username || "",
          d = e.auth.password ? unescape(encodeURIComponent(e.auth.password)) : "";
        i.set("Authorization", "Basic " + btoa(A + ":" + d));
      }
      var f = pt(e.baseURL, e.url);
      c.open(e.method.toUpperCase(), ft(f, e.params, e.paramsSerializer), !0), c.timeout = e.timeout;
      function m() {
        if (!c) return;
        var A = B.from("getAllResponseHeaders" in c && c.getAllResponseHeaders()),
          h = {
            data: !o || o === "text" || o === "json" ? c.responseText : c.response,
            status: c.status,
            statusText: c.statusText,
            headers: A,
            config: e,
            request: c
          };
        Mr(function (C) {
          r(C), u();
        }, function (C) {
          n(C), u();
        }, h), c = null;
      }
      if ("onloadend" in c ? c.onloadend = m : c.onreadystatechange = function () {
        !c || c.readyState !== 4 || c.status === 0 && !(c.responseURL && c.responseURL.indexOf("file:") === 0) || setTimeout(m);
      }, c.onabort = function () {
        c && (n(new b("Request aborted", b.ECONNABORTED, e, c)), c = null);
      }, c.onerror = function () {
        n(new b("Network Error", b.ERR_NETWORK, e, c)), c = null;
      }, c.ontimeout = function () {
        var d = e.timeout ? "timeout of " + e.timeout + "ms exceeded" : "timeout exceeded";
        var h = e.transitional || dt;
        e.timeoutErrorMessage && (d = e.timeoutErrorMessage), n(new b(d, h.clarifyTimeoutError ? b.ETIMEDOUT : b.ECONNABORTED, e, c)), c = null;
      }, D.isStandardBrowserEnv) {
        var _A = (e.withCredentials || Dr(f)) && e.xsrfCookieName && vr.read(e.xsrfCookieName);
        _A && i.set(e.xsrfHeaderName, _A);
      }
      s === void 0 && i.setContentType(null), "setRequestHeader" in c && l.forEach(i.toJSON(), function (d, h) {
        c.setRequestHeader(h, d);
      }), l.isUndefined(e.withCredentials) || (c.withCredentials = !!e.withCredentials), o && o !== "json" && (c.responseType = e.responseType), typeof e.onDownloadProgress == "function" && c.addEventListener("progress", $e(e.onDownloadProgress, !0)), typeof e.onUploadProgress == "function" && c.upload && c.upload.addEventListener("progress", $e(e.onUploadProgress)), (e.cancelToken || e.signal) && (a = function a(A) {
        c && (n(!A || A.type ? new G(null, e, c) : A), c.abort(), c = null);
      }, e.cancelToken && e.cancelToken.subscribe(a), e.signal && (e.signal.aborted ? a() : e.signal.addEventListener("abort", a)));
      var y = jr(f);
      if (y && D.protocols.indexOf(y) === -1) {
        n(new b("Unsupported protocol " + y + ":", b.ERR_BAD_REQUEST, e));
        return;
      }
      c.send(s || null);
    });
  },
  Y = {
    http: fr,
    xhr: Ur
  };
l.forEach(Y, function (e, t) {
  if (e) {
    try {
      Object.defineProperty(e, "name", {
        value: t
      });
    } catch (_unused) {}
    Object.defineProperty(e, "adapterName", {
      value: t
    });
  }
});
var qr = {
  getAdapter: function getAdapter(e) {
    e = l.isArray(e) ? e : [e];
    var _e2 = e,
      t = _e2.length;
    var r, n;
    for (var s = 0; s < t && (r = e[s], !(n = l.isString(r) ? Y[r.toLowerCase()] : r)); s++);
    if (!n) throw n === !1 ? new b("Adapter ".concat(r, " is not supported by the environment"), "ERR_NOT_SUPPORT") : new Error(l.hasOwnProp(Y, r) ? "Adapter '".concat(r, "' is not available in the build") : "Unknown adapter '".concat(r, "'"));
    if (!l.isFunction(n)) throw new TypeError("adapter is not a function");
    return n;
  },
  adapters: Y
};
function Ae(e) {
  if (e.cancelToken && e.cancelToken.throwIfRequested(), e.signal && e.signal.aborted) throw new G(null, e);
}
function He(e) {
  return Ae(e), e.headers = B.from(e.headers), e.data = he.call(e, e.transformRequest), ["post", "put", "patch"].indexOf(e.method) !== -1 && e.headers.setContentType("application/x-www-form-urlencoded", !1), qr.getAdapter(e.adapter || Ne.adapter)(e).then(function (n) {
    return Ae(e), n.data = he.call(e, e.transformResponse, n), n.headers = B.from(n.headers), n;
  }, function (n) {
    return gt(n) || (Ae(e), n && n.response && (n.response.data = he.call(e, e.transformResponse, n.response), n.response.headers = B.from(n.response.headers))), Promise.reject(n);
  });
}
var Je = function Je(e) {
  return e instanceof B ? e.toJSON() : e;
};
function H(e, t) {
  t = t || {};
  var r = {};
  function n(c, f, m) {
    return l.isPlainObject(c) && l.isPlainObject(f) ? l.merge.call({
      caseless: m
    }, c, f) : l.isPlainObject(f) ? l.merge({}, f) : l.isArray(f) ? f.slice() : f;
  }
  function s(c, f, m) {
    if (l.isUndefined(f)) {
      if (!l.isUndefined(c)) return n(void 0, c, m);
    } else return n(c, f, m);
  }
  function i(c, f) {
    if (!l.isUndefined(f)) return n(void 0, f);
  }
  function o(c, f) {
    if (l.isUndefined(f)) {
      if (!l.isUndefined(c)) return n(void 0, c);
    } else return n(void 0, f);
  }
  function a(c, f, m) {
    if (m in t) return n(c, f);
    if (m in e) return n(void 0, c);
  }
  var u = {
    url: i,
    method: i,
    data: i,
    baseURL: o,
    transformRequest: o,
    transformResponse: o,
    paramsSerializer: o,
    timeout: o,
    timeoutMessage: o,
    withCredentials: o,
    adapter: o,
    responseType: o,
    xsrfCookieName: o,
    xsrfHeaderName: o,
    onUploadProgress: o,
    onDownloadProgress: o,
    decompress: o,
    maxContentLength: o,
    maxBodyLength: o,
    beforeRedirect: o,
    transport: o,
    httpAgent: o,
    httpsAgent: o,
    cancelToken: o,
    socketPath: o,
    responseEncoding: o,
    validateStatus: a,
    headers: function headers(c, f) {
      return s(Je(c), Je(f), !0);
    }
  };
  return l.forEach(Object.keys(Object.assign({}, e, t)), function (f) {
    var m = u[f] || s,
      y = m(e[f], t[f], f);
    l.isUndefined(y) && m !== a || (r[f] = y);
  }), r;
}
var ht = "1.4.0",
  ke = {};
["object", "boolean", "number", "function", "string", "symbol"].forEach(function (e, t) {
  ke[e] = function (n) {
    return _typeof(n) === e || "a" + (t < 1 ? "n " : " ") + e;
  };
});
var ze = {};
ke.transitional = function (t, r, n) {
  function s(i, o) {
    return "[Axios v" + ht + "] Transitional option '" + i + "'" + o + (n ? ". " + n : "");
  }
  return function (i, o, a) {
    if (t === !1) throw new b(s(o, " has been removed" + (r ? " in " + r : "")), b.ERR_DEPRECATED);
    return r && !ze[o] && (ze[o] = !0, console.warn(s(o, " has been deprecated since v" + r + " and will be removed in the near future"))), t ? t(i, o, a) : !0;
  };
};
function $r(e, t, r) {
  if (_typeof(e) != "object") throw new b("options must be an object", b.ERR_BAD_OPTION_VALUE);
  var n = Object.keys(e);
  var s = n.length;
  for (; s-- > 0;) {
    var i = n[s],
      o = t[i];
    if (o) {
      var a = e[i],
        u = a === void 0 || o(a, i, e);
      if (u !== !0) throw new b("option " + i + " must be " + u, b.ERR_BAD_OPTION_VALUE);
      continue;
    }
    if (r !== !0) throw new b("Unknown option " + i, b.ERR_BAD_OPTION);
  }
}
var Ee = {
    assertOptions: $r,
    validators: ke
  },
  L = Ee.validators;
var te = /*#__PURE__*/function () {
  function te(t) {
    _classCallCheck(this, te);
    this.defaults = t, this.interceptors = {
      request: new Ue(),
      response: new Ue()
    };
  }
  _createClass(te, [{
    key: "request",
    value: function request(t, r) {
      typeof t == "string" ? (r = r || {}, r.url = t) : r = t || {}, r = H(this.defaults, r);
      var _r2 = r,
        n = _r2.transitional,
        s = _r2.paramsSerializer,
        i = _r2.headers;
      n !== void 0 && Ee.assertOptions(n, {
        silentJSONParsing: L.transitional(L.boolean),
        forcedJSONParsing: L.transitional(L.boolean),
        clarifyTimeoutError: L.transitional(L.boolean)
      }, !1), s != null && (l.isFunction(s) ? r.paramsSerializer = {
        serialize: s
      } : Ee.assertOptions(s, {
        encode: L.function,
        serialize: L.function
      }, !0)), r.method = (r.method || this.defaults.method || "get").toLowerCase();
      var o;
      o = i && l.merge(i.common, i[r.method]), o && l.forEach(["delete", "get", "head", "post", "put", "patch", "common"], function (d) {
        delete i[d];
      }), r.headers = B.concat(o, i);
      var a = [];
      var u = !0;
      this.interceptors.request.forEach(function (h) {
        typeof h.runWhen == "function" && h.runWhen(r) === !1 || (u = u && h.synchronous, a.unshift(h.fulfilled, h.rejected));
      });
      var c = [];
      this.interceptors.response.forEach(function (h) {
        c.push(h.fulfilled, h.rejected);
      });
      var f,
        m = 0,
        y;
      if (!u) {
        var d = [He.bind(this), void 0];
        for (d.unshift.apply(d, a), d.push.apply(d, c), y = d.length, f = Promise.resolve(r); m < y;) f = f.then(d[m++], d[m++]);
        return f;
      }
      y = a.length;
      var A = r;
      for (m = 0; m < y;) {
        var _d2 = a[m++],
          h = a[m++];
        try {
          A = _d2(A);
        } catch (S) {
          h.call(this, S);
          break;
        }
      }
      try {
        f = He.call(this, A);
      } catch (d) {
        return Promise.reject(d);
      }
      for (m = 0, y = c.length; m < y;) f = f.then(c[m++], c[m++]);
      return f;
    }
  }, {
    key: "getUri",
    value: function getUri(t) {
      t = H(this.defaults, t);
      var r = pt(t.baseURL, t.url);
      return ft(r, t.params, t.paramsSerializer);
    }
  }]);
  return te;
}();
l.forEach(["delete", "get", "head", "options"], function (t) {
  te.prototype[t] = function (r, n) {
    return this.request(H(n || {}, {
      method: t,
      url: r,
      data: (n || {}).data
    }));
  };
});
l.forEach(["post", "put", "patch"], function (t) {
  function r(n) {
    return function (i, o, a) {
      return this.request(H(a || {}, {
        method: t,
        headers: n ? {
          "Content-Type": "multipart/form-data"
        } : {},
        url: i,
        data: o
      }));
    };
  }
  te.prototype[t] = r(), te.prototype[t + "Form"] = r(!0);
});
var ee = te;
var _e = /*#__PURE__*/function () {
  function _e(t) {
    _classCallCheck(this, _e);
    if (typeof t != "function") throw new TypeError("executor must be a function.");
    var r;
    this.promise = new Promise(function (i) {
      r = i;
    });
    var n = this;
    this.promise.then(function (s) {
      if (!n._listeners) return;
      var i = n._listeners.length;
      for (; i-- > 0;) n._listeners[i](s);
      n._listeners = null;
    }), this.promise.then = function (s) {
      var i;
      var o = new Promise(function (a) {
        n.subscribe(a), i = a;
      }).then(s);
      return o.cancel = function () {
        n.unsubscribe(i);
      }, o;
    }, t(function (i, o, a) {
      n.reason || (n.reason = new G(i, o, a), r(n.reason));
    });
  }
  _createClass(_e, [{
    key: "throwIfRequested",
    value: function throwIfRequested() {
      if (this.reason) throw this.reason;
    }
  }, {
    key: "subscribe",
    value: function subscribe(t) {
      if (this.reason) {
        t(this.reason);
        return;
      }
      this._listeners ? this._listeners.push(t) : this._listeners = [t];
    }
  }, {
    key: "unsubscribe",
    value: function unsubscribe(t) {
      if (!this._listeners) return;
      var r = this._listeners.indexOf(t);
      r !== -1 && this._listeners.splice(r, 1);
    }
  }], [{
    key: "source",
    value: function source() {
      var t;
      return {
        token: new _e(function (s) {
          t = s;
        }),
        cancel: t
      };
    }
  }]);
  return _e;
}();
var Hr = _e;
function Jr(e) {
  return function (r) {
    return e.apply(null, r);
  };
}
function zr(e) {
  return l.isObject(e) && e.isAxiosError === !0;
}
var Se = {
  Continue: 100,
  SwitchingProtocols: 101,
  Processing: 102,
  EarlyHints: 103,
  Ok: 200,
  Created: 201,
  Accepted: 202,
  NonAuthoritativeInformation: 203,
  NoContent: 204,
  ResetContent: 205,
  PartialContent: 206,
  MultiStatus: 207,
  AlreadyReported: 208,
  ImUsed: 226,
  MultipleChoices: 300,
  MovedPermanently: 301,
  Found: 302,
  SeeOther: 303,
  NotModified: 304,
  UseProxy: 305,
  Unused: 306,
  TemporaryRedirect: 307,
  PermanentRedirect: 308,
  BadRequest: 400,
  Unauthorized: 401,
  PaymentRequired: 402,
  Forbidden: 403,
  NotFound: 404,
  MethodNotAllowed: 405,
  NotAcceptable: 406,
  ProxyAuthenticationRequired: 407,
  RequestTimeout: 408,
  Conflict: 409,
  Gone: 410,
  LengthRequired: 411,
  PreconditionFailed: 412,
  PayloadTooLarge: 413,
  UriTooLong: 414,
  UnsupportedMediaType: 415,
  RangeNotSatisfiable: 416,
  ExpectationFailed: 417,
  ImATeapot: 418,
  MisdirectedRequest: 421,
  UnprocessableEntity: 422,
  Locked: 423,
  FailedDependency: 424,
  TooEarly: 425,
  UpgradeRequired: 426,
  PreconditionRequired: 428,
  TooManyRequests: 429,
  RequestHeaderFieldsTooLarge: 431,
  UnavailableForLegalReasons: 451,
  InternalServerError: 500,
  NotImplemented: 501,
  BadGateway: 502,
  ServiceUnavailable: 503,
  GatewayTimeout: 504,
  HttpVersionNotSupported: 505,
  VariantAlsoNegotiates: 506,
  InsufficientStorage: 507,
  LoopDetected: 508,
  NotExtended: 510,
  NetworkAuthenticationRequired: 511
};
Object.entries(Se).forEach(function (_ref7) {
  var _ref8 = _slicedToArray(_ref7, 2),
    e = _ref8[0],
    t = _ref8[1];
  Se[t] = e;
});
var Wr = Se;
function At(e) {
  var t = new ee(e),
    r = Ye(ee.prototype.request, t);
  return l.extend(r, ee.prototype, t, {
    allOwnKeys: !0
  }), l.extend(r, t, null, {
    allOwnKeys: !0
  }), r.create = function (s) {
    return At(H(e, s));
  }, r;
}
var O = At(Ne);
O.Axios = ee;
O.CanceledError = G;
O.CancelToken = Hr;
O.isCancel = gt;
O.VERSION = ht;
O.toFormData = ae;
O.AxiosError = b;
O.Cancel = O.CanceledError;
O.all = function (t) {
  return Promise.all(t);
};
O.spread = Jr;
O.isAxiosError = zr;
O.mergeConfig = H;
O.AxiosHeaders = B;
O.formToJSON = function (e) {
  return mt(l.isHTMLForm(e) ? new FormData(e) : e);
};
O.HttpStatusCode = Wr;
O.default = O;
var We = O,
  Ve = "https://kdocs.cn",
  yt = /*#__PURE__*/function () {
    var _ref9 = _asyncToGenerator( /*#__PURE__*/_regeneratorRuntime().mark(function _callee(e) {
      var t, r;
      return _regeneratorRuntime().wrap(function _callee$(_context) {
        while (1) switch (_context.prev = _context.next) {
          case 0:
            _context.prev = 0;
            _context.next = 3;
            return U.cookies.get({
              url: Ve,
              name: "csrf"
            });
          case 3:
            t = _context.sent;
            if (!(t != null && t.value)) {
              _context.next = 8;
              break;
            }
            e["X-CSRFToken"] = t.value;
            _context.next = 12;
            break;
          case 8:
            r = Vr();
            _context.next = 11;
            return U.cookies.set({
              url: Ve,
              name: "csrf",
              value: r,
              domain: ".kdocs.cn",
              path: "/",
              secure: !1,
              storeId: "0",
              httpOnly: !1
            });
          case 11:
            e["X-CSRFToken"] = r;
          case 12:
            _context.next = 16;
            break;
          case 14:
            _context.prev = 14;
            _context.t0 = _context["catch"](0);
          case 16:
            return _context.abrupt("return", e);
          case 17:
          case "end":
            return _context.stop();
        }
      }, _callee, null, [[0, 14]]);
    }));
    return function yt(_x2) {
      return _ref9.apply(this, arguments);
    };
  }();
function Vr() {
  var e = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678",
    t = e.length;
  var r = "";
  for (var n = 0; n < 32; n++) r += e.charAt(Math.floor(Math.random() * t));
  return r;
}
var Kr = {
    timeout: 1e4,
    headers: {
      Accept: "application/json, text/plain, */*",
      "Content-Type": "application/json"
    },
    withCredentials: !0
  },
  v = /*#__PURE__*/function () {
    function v() {
      _classCallCheck(this, v);
      this.httpInterceptorsRequest(), this.httpInterceptorsResponse();
    }
    _createClass(v, [{
      key: "httpInterceptorsRequest",
      value: function httpInterceptorsRequest() {
        v.axiosInstance.interceptors.request.use(function (t) {
          return typeof t.beforeRequestCallback == "function" ? (t.beforeRequestCallback(t), t) : (v.initConfig.beforeRequestCallback && v.initConfig.beforeRequestCallback(t), t);
        }, function (t) {
          return Promise.reject(t);
        });
      }
    }, {
      key: "httpInterceptorsResponse",
      value: function httpInterceptorsResponse() {
        v.axiosInstance.interceptors.response.use(function (r) {
          var n = r.config;
          return typeof n.beforeResponseCallback == "function" ? (n.beforeResponseCallback(r), r.data) : (v.initConfig.beforeResponseCallback && v.initConfig.beforeResponseCallback(r), r.data);
        }, function (r) {
          var n = r;
          return n.isCancelRequest = We.isCancel(n), Promise.reject(n);
        });
      }
    }, {
      key: "request",
      value: function request(t, r, n, s) {
        var i = _objectSpread(_objectSpread({
          method: t,
          url: r
        }, n), s);
        return new Promise( /*#__PURE__*/function () {
          var _ref10 = _asyncToGenerator( /*#__PURE__*/_regeneratorRuntime().mark(function _callee2(o, a) {
            return _regeneratorRuntime().wrap(function _callee2$(_context2) {
              while (1) switch (_context2.prev = _context2.next) {
                case 0:
                  _context2.next = 2;
                  return yt((n == null ? void 0 : n.headers) || {});
                case 2:
                  i.headers = _context2.sent;
                  v.axiosInstance.request(i).then(function (u) {
                    o(u);
                  }).catch(function (u) {
                    a(u);
                  });
                case 4:
                case "end":
                  return _context2.stop();
              }
            }, _callee2);
          }));
          return function (_x3, _x4) {
            return _ref10.apply(this, arguments);
          };
        }());
      }
    }]);
    return v;
  }();
me(v, "initConfig", {}), me(v, "axiosInstance", We.create(Kr));
var Oe = v;
var Gr = new Oe();
var Xr = /*#__PURE__*/function () {
  function Xr() {
    _classCallCheck(this, Xr);
  }
  _createClass(Xr, [{
    key: "request",
    value: function request(t, r, n) {
      return new Promise( /*#__PURE__*/function () {
        var _ref11 = _asyncToGenerator( /*#__PURE__*/_regeneratorRuntime().mark(function _callee4(s, i) {
          var o, a;
          return _regeneratorRuntime().wrap(function _callee4$(_context4) {
            while (1) switch (_context4.prev = _context4.next) {
              case 0:
                o = {
                  method: (t == null ? void 0 : t.toUpperCase()) || "GET",
                  mode: "cors",
                  credentials: "include"
                };
                _context4.next = 3;
                return yt((n == null ? void 0 : n.headers) || {});
              case 3:
                a = _context4.sent;
                o.headers = _objectSpread({
                  Accept: "application/json, text/plain, */*",
                  "Content-Type": "application/json"
                }, a || {});
                try {
                  a["Content-Type"] === "multipart/form-data" ? (o.body = n == null ? void 0 : n.data, o.headers && delete o.headers["Content-Type"]) : n != null && n.data && (o.body = JSON.stringify(n.data));
                } catch (_unused3) {}
                fetch(r, o).then( /*#__PURE__*/function () {
                  var _ref12 = _asyncToGenerator( /*#__PURE__*/_regeneratorRuntime().mark(function _callee3(u) {
                    var c;
                    return _regeneratorRuntime().wrap(function _callee3$(_context3) {
                      while (1) switch (_context3.prev = _context3.next) {
                        case 0:
                          _context3.prev = 0;
                          _context3.next = 3;
                          return u.json();
                        case 3:
                          c = _context3.sent;
                          _context3.next = 9;
                          break;
                        case 6:
                          _context3.prev = 6;
                          _context3.t0 = _context3["catch"](0);
                          c = u;
                        case 9:
                          if (!(u.status !== 200)) {
                            _context3.next = 11;
                            break;
                          }
                          throw {
                            response: c
                          };
                        case 11:
                          return _context3.abrupt("return", c);
                        case 12:
                        case "end":
                          return _context3.stop();
                      }
                    }, _callee3, null, [[0, 6]]);
                  }));
                  return function (_x7) {
                    return _ref12.apply(this, arguments);
                  };
                }()).then(function (u) {
                  s(u);
                }).catch(function (u) {
                  i(u);
                });
              case 7:
              case "end":
                return _context4.stop();
            }
          }, _callee4);
        }));
        return function (_x5, _x6) {
          return _ref11.apply(this, arguments);
        };
      }());
    }
  }]);
  return Xr;
}();
var Zr = new Xr(),
  Qr = function Qr() {
    return typeof XMLHttpRequest == "function" ? Gr : Zr;
  },
  wt = Qr(),
  Yr = function Yr() {
    return wt.request("get", Qe + "/kd/api/old_user");
  },
  en = function en() {
    return wt.request("post", Qe + "/kd/api/old_user");
  },
  _n = function _n(e) {
    U.storage.local.set(_defineProperty({}, Te, JSON.stringify(e))).catch(function () {});
  },
  tn = /*#__PURE__*/function () {
    var _ref13 = _asyncToGenerator( /*#__PURE__*/_regeneratorRuntime().mark(function _callee5() {
      var e, t;
      return _regeneratorRuntime().wrap(function _callee5$(_context5) {
        while (1) switch (_context5.prev = _context5.next) {
          case 0:
            _context5.prev = 0;
            e = Te;
            _context5.next = 4;
            return U.storage.local.get(e);
          case 4:
            _context5.t0 = e;
            t = _context5.sent[_context5.t0];
            return _context5.abrupt("return", JSON.parse(t));
          case 9:
            _context5.prev = 9;
            _context5.t1 = _context5["catch"](0);
          case 11:
            return _context5.abrupt("return", null);
          case 12:
          case "end":
            return _context5.stop();
        }
      }, _callee5, null, [[0, 9]]);
    }));
    return function tn() {
      return _ref13.apply(this, arguments);
    };
  }(),
  Mn = function Mn() {
    U.storage.local.remove(Te).catch(function () {});
  },
  rn = /*#__PURE__*/function () {
    var _ref14 = _asyncToGenerator( /*#__PURE__*/_regeneratorRuntime().mark(function _callee6() {
      var e, t;
      return _regeneratorRuntime().wrap(function _callee6$(_context6) {
        while (1) switch (_context6.prev = _context6.next) {
          case 0:
            _context6.prev = 0;
            e = Xe;
            _context6.next = 4;
            return U.storage.local.get(e);
          case 4:
            _context6.t0 = e;
            t = _context6.sent[_context6.t0];
            return _context6.abrupt("return", JSON.parse(t));
          case 9:
            _context6.prev = 9;
            _context6.t1 = _context6["catch"](0);
          case 11:
            return _context6.abrupt("return", null);
          case 12:
          case "end":
            return _context6.stop();
        }
      }, _callee6, null, [[0, 9]]);
    }));
    return function rn() {
      return _ref14.apply(this, arguments);
    };
  }(),
  vn = /*#__PURE__*/function () {
    var _ref15 = _asyncToGenerator( /*#__PURE__*/_regeneratorRuntime().mark(function _callee7() {
      var e, t, r, n, s, i;
      return _regeneratorRuntime().wrap(function _callee7$(_context7) {
        while (1) switch (_context7.prev = _context7.next) {
          case 0:
            _context7.prev = 0;
            _context7.next = 3;
            return tn();
          case 3:
            r = _context7.sent;
            n = ((e = r == null ? void 0 : r.userid) == null ? void 0 : e.toString()) || "";
            _context7.next = 7;
            return rn();
          case 7:
            _context7.t0 = _context7.sent;
            if (_context7.t0) {
              _context7.next = 10;
              break;
            }
            _context7.t0 = {};
          case 10:
            s = _context7.t0;
            if (!((s == null ? void 0 : s[n]) === "true")) {
              _context7.next = 13;
              break;
            }
            return _context7.abrupt("return", "0");
          case 13:
            _context7.next = 15;
            return Yr();
          case 15:
            i = _context7.sent;
            s[n] = "true";
            U.storage.local.set(_defineProperty({}, Xe, JSON.stringify(s))).catch(function () {});
            if (!((t = i == null ? void 0 : i.data) != null && t.isOldUser)) {
              _context7.next = 22;
              break;
            }
            _context7.t1 = "0";
            _context7.next = 25;
            break;
          case 22:
            _context7.next = 24;
            return en();
          case 24:
            _context7.t1 = "1";
          case 25:
            return _context7.abrupt("return", _context7.t1);
          case 28:
            _context7.prev = 28;
            _context7.t2 = _context7["catch"](0);
            return _context7.abrupt("return", "");
          case 31:
          case "end":
            return _context7.stop();
        }
      }, _callee7, null, [[0, 28]]);
    }));
    return function vn() {
      return _ref15.apply(this, arguments);
    };
  }();
var Me = {
  exports: {}
};
var nn = function nn(e) {
    return (typeof crypto === "undefined" ? "undefined" : _typeof(crypto)) < "u" && typeof crypto.getRandomValues == "function" ? function () {
      var t = crypto.getRandomValues(new Uint8Array(1))[0];
      return (t >= e ? t % e : t).toString(e);
    } : function () {
      return Math.floor(Math.random() * e).toString(e);
    };
  },
  bt = function bt() {
    var e = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : 7;
    var t = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : !1;
    return Array.from({
      length: e
    }, nn(t ? 16 : 36)).join("");
  };
Me.exports = bt;
Me.exports.default = bt;
var sn = Me.exports;
var re = Ze(sn);
var on = function on() {
    return "uid::".concat(re(7));
  },
  an = function an(e) {
    var t = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : ["endpointName", "fingerprint"];
    return _typeof(e) == "object" && e !== null && t.every(function (r) {
      return r in e;
    });
  },
  cn = function cn(e) {
    if (!an(e)) throw new TypeError("Invalid connection args");
    return JSON.stringify(e);
  },
  ln = function ln() {
    var e = [];
    return {
      add: function add() {
        for (var _len3 = arguments.length, t = new Array(_len3), _key3 = 0; _key3 < _len3; _key3++) {
          t[_key3] = arguments[_key3];
        }
        e = [].concat(_toConsumableArray(e), t);
      },
      remove: function remove(t) {
        e = typeof t == "string" ? e.filter(function (r) {
          return r.message.transactionId !== t;
        }) : e.filter(function (r) {
          return !t.includes(r);
        });
      },
      entries: function entries() {
        return e;
      }
    };
  },
  ye = /*#__PURE__*/function () {
    function ye() {
      _classCallCheck(this, ye);
    }
    _createClass(ye, null, [{
      key: "toBackground",
      value: function toBackground(e, t) {
        return e.postMessage(t);
      }
    }, {
      key: "toExtensionContext",
      value: function toExtensionContext(e, t) {
        return e.postMessage(t);
      }
    }]);
    return ye;
  }(),
  xt = {
    exports: {}
  };
(function (e, t) {
  (function (r, n) {
    n(e);
  })((typeof globalThis === "undefined" ? "undefined" : _typeof(globalThis)) < "u" ? globalThis : (typeof self === "undefined" ? "undefined" : _typeof(self)) < "u" ? self : kt, function (r) {
    if ((typeof globalThis === "undefined" ? "undefined" : _typeof(globalThis)) != "object" || (typeof chrome === "undefined" ? "undefined" : _typeof(chrome)) != "object" || !chrome || !chrome.runtime || !chrome.runtime.id) throw new Error("This script should only be loaded in a browser extension.");
    if (_typeof(globalThis.browser) > "u" || Object.getPrototypeOf(globalThis.browser) !== Object.prototype) {
      var n = "The message port closed before a response was received.",
        s = "Returning a Promise is the preferred way to send a reply from an onMessage/onMessageExternal listener, as the sendResponse will be removed from the specs (See https://developer.mozilla.org/docs/Mozilla/Add-ons/WebExtensions/API/runtime/onMessage)",
        i = function i(o) {
          var a = {
            alarms: {
              clear: {
                minArgs: 0,
                maxArgs: 1
              },
              clearAll: {
                minArgs: 0,
                maxArgs: 0
              },
              get: {
                minArgs: 0,
                maxArgs: 1
              },
              getAll: {
                minArgs: 0,
                maxArgs: 0
              }
            },
            bookmarks: {
              create: {
                minArgs: 1,
                maxArgs: 1
              },
              get: {
                minArgs: 1,
                maxArgs: 1
              },
              getChildren: {
                minArgs: 1,
                maxArgs: 1
              },
              getRecent: {
                minArgs: 1,
                maxArgs: 1
              },
              getSubTree: {
                minArgs: 1,
                maxArgs: 1
              },
              getTree: {
                minArgs: 0,
                maxArgs: 0
              },
              move: {
                minArgs: 2,
                maxArgs: 2
              },
              remove: {
                minArgs: 1,
                maxArgs: 1
              },
              removeTree: {
                minArgs: 1,
                maxArgs: 1
              },
              search: {
                minArgs: 1,
                maxArgs: 1
              },
              update: {
                minArgs: 2,
                maxArgs: 2
              }
            },
            browserAction: {
              disable: {
                minArgs: 0,
                maxArgs: 1,
                fallbackToNoCallback: !0
              },
              enable: {
                minArgs: 0,
                maxArgs: 1,
                fallbackToNoCallback: !0
              },
              getBadgeBackgroundColor: {
                minArgs: 1,
                maxArgs: 1
              },
              getBadgeText: {
                minArgs: 1,
                maxArgs: 1
              },
              getPopup: {
                minArgs: 1,
                maxArgs: 1
              },
              getTitle: {
                minArgs: 1,
                maxArgs: 1
              },
              openPopup: {
                minArgs: 0,
                maxArgs: 0
              },
              setBadgeBackgroundColor: {
                minArgs: 1,
                maxArgs: 1,
                fallbackToNoCallback: !0
              },
              setBadgeText: {
                minArgs: 1,
                maxArgs: 1,
                fallbackToNoCallback: !0
              },
              setIcon: {
                minArgs: 1,
                maxArgs: 1
              },
              setPopup: {
                minArgs: 1,
                maxArgs: 1,
                fallbackToNoCallback: !0
              },
              setTitle: {
                minArgs: 1,
                maxArgs: 1,
                fallbackToNoCallback: !0
              }
            },
            browsingData: {
              remove: {
                minArgs: 2,
                maxArgs: 2
              },
              removeCache: {
                minArgs: 1,
                maxArgs: 1
              },
              removeCookies: {
                minArgs: 1,
                maxArgs: 1
              },
              removeDownloads: {
                minArgs: 1,
                maxArgs: 1
              },
              removeFormData: {
                minArgs: 1,
                maxArgs: 1
              },
              removeHistory: {
                minArgs: 1,
                maxArgs: 1
              },
              removeLocalStorage: {
                minArgs: 1,
                maxArgs: 1
              },
              removePasswords: {
                minArgs: 1,
                maxArgs: 1
              },
              removePluginData: {
                minArgs: 1,
                maxArgs: 1
              },
              settings: {
                minArgs: 0,
                maxArgs: 0
              }
            },
            commands: {
              getAll: {
                minArgs: 0,
                maxArgs: 0
              }
            },
            contextMenus: {
              remove: {
                minArgs: 1,
                maxArgs: 1
              },
              removeAll: {
                minArgs: 0,
                maxArgs: 0
              },
              update: {
                minArgs: 2,
                maxArgs: 2
              }
            },
            cookies: {
              get: {
                minArgs: 1,
                maxArgs: 1
              },
              getAll: {
                minArgs: 1,
                maxArgs: 1
              },
              getAllCookieStores: {
                minArgs: 0,
                maxArgs: 0
              },
              remove: {
                minArgs: 1,
                maxArgs: 1
              },
              set: {
                minArgs: 1,
                maxArgs: 1
              }
            },
            devtools: {
              inspectedWindow: {
                eval: {
                  minArgs: 1,
                  maxArgs: 2,
                  singleCallbackArg: !1
                }
              },
              panels: {
                create: {
                  minArgs: 3,
                  maxArgs: 3,
                  singleCallbackArg: !0
                },
                elements: {
                  createSidebarPane: {
                    minArgs: 1,
                    maxArgs: 1
                  }
                }
              }
            },
            downloads: {
              cancel: {
                minArgs: 1,
                maxArgs: 1
              },
              download: {
                minArgs: 1,
                maxArgs: 1
              },
              erase: {
                minArgs: 1,
                maxArgs: 1
              },
              getFileIcon: {
                minArgs: 1,
                maxArgs: 2
              },
              open: {
                minArgs: 1,
                maxArgs: 1,
                fallbackToNoCallback: !0
              },
              pause: {
                minArgs: 1,
                maxArgs: 1
              },
              removeFile: {
                minArgs: 1,
                maxArgs: 1
              },
              resume: {
                minArgs: 1,
                maxArgs: 1
              },
              search: {
                minArgs: 1,
                maxArgs: 1
              },
              show: {
                minArgs: 1,
                maxArgs: 1,
                fallbackToNoCallback: !0
              }
            },
            extension: {
              isAllowedFileSchemeAccess: {
                minArgs: 0,
                maxArgs: 0
              },
              isAllowedIncognitoAccess: {
                minArgs: 0,
                maxArgs: 0
              }
            },
            history: {
              addUrl: {
                minArgs: 1,
                maxArgs: 1
              },
              deleteAll: {
                minArgs: 0,
                maxArgs: 0
              },
              deleteRange: {
                minArgs: 1,
                maxArgs: 1
              },
              deleteUrl: {
                minArgs: 1,
                maxArgs: 1
              },
              getVisits: {
                minArgs: 1,
                maxArgs: 1
              },
              search: {
                minArgs: 1,
                maxArgs: 1
              }
            },
            i18n: {
              detectLanguage: {
                minArgs: 1,
                maxArgs: 1
              },
              getAcceptLanguages: {
                minArgs: 0,
                maxArgs: 0
              }
            },
            identity: {
              launchWebAuthFlow: {
                minArgs: 1,
                maxArgs: 1
              }
            },
            idle: {
              queryState: {
                minArgs: 1,
                maxArgs: 1
              }
            },
            management: {
              get: {
                minArgs: 1,
                maxArgs: 1
              },
              getAll: {
                minArgs: 0,
                maxArgs: 0
              },
              getSelf: {
                minArgs: 0,
                maxArgs: 0
              },
              setEnabled: {
                minArgs: 2,
                maxArgs: 2
              },
              uninstallSelf: {
                minArgs: 0,
                maxArgs: 1
              }
            },
            notifications: {
              clear: {
                minArgs: 1,
                maxArgs: 1
              },
              create: {
                minArgs: 1,
                maxArgs: 2
              },
              getAll: {
                minArgs: 0,
                maxArgs: 0
              },
              getPermissionLevel: {
                minArgs: 0,
                maxArgs: 0
              },
              update: {
                minArgs: 2,
                maxArgs: 2
              }
            },
            pageAction: {
              getPopup: {
                minArgs: 1,
                maxArgs: 1
              },
              getTitle: {
                minArgs: 1,
                maxArgs: 1
              },
              hide: {
                minArgs: 1,
                maxArgs: 1,
                fallbackToNoCallback: !0
              },
              setIcon: {
                minArgs: 1,
                maxArgs: 1
              },
              setPopup: {
                minArgs: 1,
                maxArgs: 1,
                fallbackToNoCallback: !0
              },
              setTitle: {
                minArgs: 1,
                maxArgs: 1,
                fallbackToNoCallback: !0
              },
              show: {
                minArgs: 1,
                maxArgs: 1,
                fallbackToNoCallback: !0
              }
            },
            permissions: {
              contains: {
                minArgs: 1,
                maxArgs: 1
              },
              getAll: {
                minArgs: 0,
                maxArgs: 0
              },
              remove: {
                minArgs: 1,
                maxArgs: 1
              },
              request: {
                minArgs: 1,
                maxArgs: 1
              }
            },
            runtime: {
              getBackgroundPage: {
                minArgs: 0,
                maxArgs: 0
              },
              getPlatformInfo: {
                minArgs: 0,
                maxArgs: 0
              },
              openOptionsPage: {
                minArgs: 0,
                maxArgs: 0
              },
              requestUpdateCheck: {
                minArgs: 0,
                maxArgs: 0
              },
              sendMessage: {
                minArgs: 1,
                maxArgs: 3
              },
              sendNativeMessage: {
                minArgs: 2,
                maxArgs: 2
              },
              setUninstallURL: {
                minArgs: 1,
                maxArgs: 1
              }
            },
            sessions: {
              getDevices: {
                minArgs: 0,
                maxArgs: 1
              },
              getRecentlyClosed: {
                minArgs: 0,
                maxArgs: 1
              },
              restore: {
                minArgs: 0,
                maxArgs: 1
              }
            },
            storage: {
              local: {
                clear: {
                  minArgs: 0,
                  maxArgs: 0
                },
                get: {
                  minArgs: 0,
                  maxArgs: 1
                },
                getBytesInUse: {
                  minArgs: 0,
                  maxArgs: 1
                },
                remove: {
                  minArgs: 1,
                  maxArgs: 1
                },
                set: {
                  minArgs: 1,
                  maxArgs: 1
                }
              },
              managed: {
                get: {
                  minArgs: 0,
                  maxArgs: 1
                },
                getBytesInUse: {
                  minArgs: 0,
                  maxArgs: 1
                }
              },
              sync: {
                clear: {
                  minArgs: 0,
                  maxArgs: 0
                },
                get: {
                  minArgs: 0,
                  maxArgs: 1
                },
                getBytesInUse: {
                  minArgs: 0,
                  maxArgs: 1
                },
                remove: {
                  minArgs: 1,
                  maxArgs: 1
                },
                set: {
                  minArgs: 1,
                  maxArgs: 1
                }
              }
            },
            tabs: {
              captureVisibleTab: {
                minArgs: 0,
                maxArgs: 2
              },
              create: {
                minArgs: 1,
                maxArgs: 1
              },
              detectLanguage: {
                minArgs: 0,
                maxArgs: 1
              },
              discard: {
                minArgs: 0,
                maxArgs: 1
              },
              duplicate: {
                minArgs: 1,
                maxArgs: 1
              },
              executeScript: {
                minArgs: 1,
                maxArgs: 2
              },
              get: {
                minArgs: 1,
                maxArgs: 1
              },
              getCurrent: {
                minArgs: 0,
                maxArgs: 0
              },
              getZoom: {
                minArgs: 0,
                maxArgs: 1
              },
              getZoomSettings: {
                minArgs: 0,
                maxArgs: 1
              },
              goBack: {
                minArgs: 0,
                maxArgs: 1
              },
              goForward: {
                minArgs: 0,
                maxArgs: 1
              },
              highlight: {
                minArgs: 1,
                maxArgs: 1
              },
              insertCSS: {
                minArgs: 1,
                maxArgs: 2
              },
              move: {
                minArgs: 2,
                maxArgs: 2
              },
              query: {
                minArgs: 1,
                maxArgs: 1
              },
              reload: {
                minArgs: 0,
                maxArgs: 2
              },
              remove: {
                minArgs: 1,
                maxArgs: 1
              },
              removeCSS: {
                minArgs: 1,
                maxArgs: 2
              },
              sendMessage: {
                minArgs: 2,
                maxArgs: 3
              },
              setZoom: {
                minArgs: 1,
                maxArgs: 2
              },
              setZoomSettings: {
                minArgs: 1,
                maxArgs: 2
              },
              update: {
                minArgs: 1,
                maxArgs: 2
              }
            },
            topSites: {
              get: {
                minArgs: 0,
                maxArgs: 0
              }
            },
            webNavigation: {
              getAllFrames: {
                minArgs: 1,
                maxArgs: 1
              },
              getFrame: {
                minArgs: 1,
                maxArgs: 1
              }
            },
            webRequest: {
              handlerBehaviorChanged: {
                minArgs: 0,
                maxArgs: 0
              }
            },
            windows: {
              create: {
                minArgs: 0,
                maxArgs: 1
              },
              get: {
                minArgs: 1,
                maxArgs: 2
              },
              getAll: {
                minArgs: 0,
                maxArgs: 1
              },
              getCurrent: {
                minArgs: 0,
                maxArgs: 1
              },
              getLastFocused: {
                minArgs: 0,
                maxArgs: 1
              },
              remove: {
                minArgs: 1,
                maxArgs: 1
              },
              update: {
                minArgs: 2,
                maxArgs: 2
              }
            }
          };
          if (Object.keys(a).length === 0) throw new Error("api-metadata.json has not been included in browser-polyfill");
          var u = /*#__PURE__*/function (_WeakMap) {
            _inherits(u, _WeakMap);
            var _super = _createSuper(u);
            function u(p) {
              var _this;
              var x = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : void 0;
              _classCallCheck(this, u);
              _this = _super.call(this, x), _this.createItem = p;
              return _this;
            }
            _createClass(u, [{
              key: "get",
              value: function get(p) {
                return this.has(p) || this.set(p, this.createItem(p)), _get(_getPrototypeOf(u.prototype), "get", this).call(this, p);
              }
            }]);
            return u;
          }( /*#__PURE__*/_wrapNativeSuper(WeakMap));
          var c = function c(g) {
              return g && _typeof(g) == "object" && typeof g.then == "function";
            },
            f = function f(g, p) {
              return function () {
                for (var _len4 = arguments.length, x = new Array(_len4), _key4 = 0; _key4 < _len4; _key4++) {
                  x[_key4] = arguments[_key4];
                }
                o.runtime.lastError ? g.reject(new Error(o.runtime.lastError.message)) : p.singleCallbackArg || x.length <= 1 && p.singleCallbackArg !== !1 ? g.resolve(x[0]) : g.resolve(x);
              };
            },
            m = function m(g) {
              return g == 1 ? "argument" : "arguments";
            },
            y = function y(g, p) {
              return function (E) {
                for (var _len5 = arguments.length, T = new Array(_len5 > 1 ? _len5 - 1 : 0), _key5 = 1; _key5 < _len5; _key5++) {
                  T[_key5 - 1] = arguments[_key5];
                }
                if (T.length < p.minArgs) throw new Error("Expected at least ".concat(p.minArgs, " ").concat(m(p.minArgs), " for ").concat(g, "(), got ").concat(T.length));
                if (T.length > p.maxArgs) throw new Error("Expected at most ".concat(p.maxArgs, " ").concat(m(p.maxArgs), " for ").concat(g, "(), got ").concat(T.length));
                return new Promise(function (P, k) {
                  if (p.fallbackToNoCallback) try {
                    E[g].apply(E, T.concat([f({
                      resolve: P,
                      reject: k
                    }, p)]));
                  } catch (w) {
                    console.warn("".concat(g, " API method doesn't seem to support the callback parameter, falling back to call it without a callback: "), w), E[g].apply(E, T), p.fallbackToNoCallback = !1, p.noCallback = !0, P();
                  } else p.noCallback ? (E[g].apply(E, T), P()) : E[g].apply(E, T.concat([f({
                    resolve: P,
                    reject: k
                  }, p)]));
                });
              };
            },
            A = function A(g, p, x) {
              return new Proxy(p, {
                apply: function apply(E, T, P) {
                  return x.call.apply(x, [T, g].concat(_toConsumableArray(P)));
                }
              });
            };
          var d = Function.call.bind(Object.prototype.hasOwnProperty);
          var h = function h(g) {
              var p = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};
              var x = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : {};
              var E = Object.create(null),
                T = {
                  has: function has(k, w) {
                    return w in g || w in E;
                  },
                  get: function get(k, w, _) {
                    if (w in E) return E[w];
                    if (!(w in g)) return;
                    var R = g[w];
                    if (typeof R == "function") {
                      if (typeof p[w] == "function") R = A(g, g[w], p[w]);else if (d(x, w)) {
                        var q = y(w, x[w]);
                        R = A(g, g[w], q);
                      } else R = R.bind(g);
                    } else if (_typeof(R) == "object" && R !== null && (d(p, w) || d(x, w))) R = h(R, p[w], x[w]);else if (d(x, "*")) R = h(R, p[w], x["*"]);else return Object.defineProperty(E, w, {
                      configurable: !0,
                      enumerable: !0,
                      get: function get() {
                        return g[w];
                      },
                      set: function set(q) {
                        g[w] = q;
                      }
                    }), R;
                    return E[w] = R, R;
                  },
                  set: function set(k, w, _, R) {
                    return w in E ? E[w] = _ : g[w] = _, !0;
                  },
                  defineProperty: function defineProperty(k, w, _) {
                    return Reflect.defineProperty(E, w, _);
                  },
                  deleteProperty: function deleteProperty(k, w) {
                    return Reflect.deleteProperty(E, w);
                  }
                },
                P = Object.create(g);
              return new Proxy(P, T);
            },
            S = function S(g) {
              return {
                addListener: function addListener(p, x) {
                  for (var _len6 = arguments.length, E = new Array(_len6 > 2 ? _len6 - 2 : 0), _key6 = 2; _key6 < _len6; _key6++) {
                    E[_key6 - 2] = arguments[_key6];
                  }
                  p.addListener.apply(p, [g.get(x)].concat(E));
                },
                hasListener: function hasListener(p, x) {
                  return p.hasListener(g.get(x));
                },
                removeListener: function removeListener(p, x) {
                  p.removeListener(g.get(x));
                }
              };
            },
            C = new u(function (g) {
              return typeof g != "function" ? g : function (x) {
                var E = h(x, {}, {
                  getContent: {
                    minArgs: 0,
                    maxArgs: 0
                  }
                });
                g(E);
              };
            });
          var N = !1;
          var I = new u(function (g) {
              return typeof g != "function" ? g : function (x, E, T) {
                var P = !1,
                  k,
                  w = new Promise(function (z) {
                    k = function k(F) {
                      N || (console.warn(s, new Error().stack), N = !0), P = !0, z(F);
                    };
                  }),
                  _;
                try {
                  _ = g(x, E, k);
                } catch (z) {
                  _ = Promise.reject(z);
                }
                var R = _ !== !0 && c(_);
                if (_ !== !0 && !R && !P) return !1;
                var q = function q(z) {
                  z.then(function (F) {
                    T(F);
                  }, function (F) {
                    var de;
                    F && (F instanceof Error || typeof F.message == "string") ? de = F.message : de = "An unexpected error occurred", T({
                      __mozWebExtensionPolyfillReject__: !0,
                      message: de
                    });
                  }).catch(function (F) {
                    console.error("Failed to send onMessage rejected reply", F);
                  });
                };
                return q(R ? _ : w), !0;
              };
            }),
            ue = function ue(_ref16, x) {
              var g = _ref16.reject,
                p = _ref16.resolve;
              o.runtime.lastError ? o.runtime.lastError.message === n ? p() : g(new Error(o.runtime.lastError.message)) : x && x.__mozWebExtensionPolyfillReject__ ? g(new Error(x.message)) : p(x);
            },
            Fe = function Fe(g, p, x) {
              for (var _len7 = arguments.length, E = new Array(_len7 > 3 ? _len7 - 3 : 0), _key7 = 3; _key7 < _len7; _key7++) {
                E[_key7 - 3] = arguments[_key7];
              }
              if (E.length < p.minArgs) throw new Error("Expected at least ".concat(p.minArgs, " ").concat(m(p.minArgs), " for ").concat(g, "(), got ").concat(E.length));
              if (E.length > p.maxArgs) throw new Error("Expected at most ".concat(p.maxArgs, " ").concat(m(p.maxArgs), " for ").concat(g, "(), got ").concat(E.length));
              return new Promise(function (T, P) {
                var k = ue.bind(null, {
                  resolve: T,
                  reject: P
                });
                E.push(k), x.sendMessage.apply(x, E);
              });
            },
            Ct = {
              devtools: {
                network: {
                  onRequestFinished: S(C)
                }
              },
              runtime: {
                onMessage: S(I),
                onMessageExternal: S(I),
                sendMessage: Fe.bind(null, "sendMessage", {
                  minArgs: 1,
                  maxArgs: 3
                })
              },
              tabs: {
                sendMessage: Fe.bind(null, "sendMessage", {
                  minArgs: 2,
                  maxArgs: 3
                })
              }
            },
            fe = {
              clear: {
                minArgs: 1,
                maxArgs: 1
              },
              get: {
                minArgs: 1,
                maxArgs: 1
              },
              set: {
                minArgs: 1,
                maxArgs: 1
              }
            };
          return a.privacy = {
            network: {
              "*": fe
            },
            services: {
              "*": fe
            },
            websites: {
              "*": fe
            }
          }, h(o, Ct, a);
        };
      r.exports = i(chrome);
    } else r.exports = globalThis.browser;
  });
})(xt);
var un = xt.exports;
var fn = Ze(un);
var dn = function dn() {
    var e = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : "";
    var t = on();
    var r,
      n = [];
    var s = ln(),
      i = new Set(),
      o = new Set(),
      a = function a(c, f) {
        switch (c.status) {
          case "undeliverable":
            n.some(function (m) {
              return m.message.messageID === c.message.messageID;
            }) || (n = [].concat(_toConsumableArray(n), [{
              message: c.message,
              resolvedDestination: c.resolvedDestination
            }]));
            return;
          case "deliverable":
            n = n.reduce(function (m, y) {
              return y.resolvedDestination === c.deliverableTo ? (ye.toBackground(f, {
                type: "deliver",
                message: y.message
              }), m) : [].concat(_toConsumableArray(m), [y]);
            }, []);
            return;
          case "delivered":
            c.receipt.message.messageType === "message" && s.add(c.receipt);
            return;
          case "incoming":
            c.message.messageType === "reply" && s.remove(c.message.messageID), i.forEach(function (m) {
              return m(c.message, f);
            });
            return;
          case "terminated":
            {
              var m = s.entries().filter(function (y) {
                return c.fingerprint === y.to;
              });
              s.remove(m), m.forEach(function (_ref17) {
                var y = _ref17.message;
                return o.forEach(function (A) {
                  return A(y);
                });
              });
            }
        }
      },
      u = function u() {
        r = fn.runtime.connect({
          name: cn({
            endpointName: e,
            fingerprint: t
          })
        }), r.onMessage.addListener(a), r.onDisconnect.addListener(u), ye.toBackground(r, {
          type: "sync",
          pendingResponses: s.entries(),
          pendingDeliveries: _toConsumableArray(new Set(n.map(function (_ref18) {
            var c = _ref18.resolvedDestination;
            return c;
          })))
        });
      };
    return u(), {
      onFailure: function onFailure(c) {
        o.add(c);
      },
      onMessage: function onMessage(c) {
        i.add(c);
      },
      postMessage: function postMessage(c) {
        ye.toBackground(r, {
          type: "deliver",
          message: c
        });
      }
    };
  },
  we,
  mn = function mn(e, t, r) {
    var _we;
    return (_we = we) !== null && _we !== void 0 ? _we : we = new Promise(function (n) {
      var s = function s(o) {
          var _o$data = o.data,
            a = _o$data.cmd,
            u = _o$data.scope,
            c = _o$data.context,
            f = o.ports;
          if (a === "webext-port-offer" && u === t && c !== e) return window.removeEventListener("message", s), f[0].onmessage = r, f[0].postMessage("port-accepted"), n(f[0]);
        },
        i = function i() {
          var o = new MessageChannel();
          o.port1.onmessage = function (a) {
            if (a.data === "port-accepted") return window.removeEventListener("message", s), n(o.port1);
            r == null || r(a);
          }, window.postMessage({
            cmd: "webext-port-offer",
            scope: t,
            context: e
          }, "*", [o.port2]);
        };
      window.addEventListener("message", s), e === "window" ? setTimeout(i, 0) : i();
    });
  },
  gn = function gn(e) {
    var t,
      r = !1,
      n,
      s;
    return {
      enable: function enable() {
        return r = !0;
      },
      onMessage: function onMessage(i) {
        return n = i;
      },
      postMessage: function () {
        var _postMessage = _asyncToGenerator( /*#__PURE__*/_regeneratorRuntime().mark(function _callee8(i) {
          return _regeneratorRuntime().wrap(function _callee8$(_context8) {
            while (1) switch (_context8.prev = _context8.next) {
              case 0:
                if (!(e !== "content-script" && e !== "window")) {
                  _context8.next = 2;
                  break;
                }
                throw new Error("Endpoint does not use postMessage");
              case 2:
                if (r) {
                  _context8.next = 4;
                  break;
                }
                throw new Error("Communication with window has not been allowed");
              case 4:
                pn(t);
                _context8.next = 7;
                return s;
              case 7:
                return _context8.abrupt("return", _context8.sent.postMessage(i));
              case 8:
              case "end":
                return _context8.stop();
            }
          }, _callee8);
        }));
        function postMessage(_x8) {
          return _postMessage.apply(this, arguments);
        }
        return postMessage;
      }(),
      setNamespace: function setNamespace(i) {
        if (t) throw new Error("Namespace once set cannot be changed");
        t = i, s = mn(e, i, function (_ref19) {
          var o = _ref19.data;
          return n == null ? void 0 : n(o);
        });
      }
    };
  };
function pn(e) {
  if (typeof e != "string" || e.trim().length === 0) throw new Error("webext-bridge uses window.postMessage to talk with other \"window\"(s) for message routingwhich is global/conflicting operation in case there are other scripts using webext-bridge. Call Bridge#setNamespace(nsps) to isolate your app. Example: setNamespace('com.facebook.react-devtools'). Make sure to use same namespace across all your scripts whereever window.postMessage is likely to be used`");
}
var hn = Object.defineProperty,
  An = Object.defineProperties,
  yn = Object.getOwnPropertyDescriptors,
  Ke = Object.getOwnPropertySymbols,
  wn = Object.prototype.hasOwnProperty,
  bn = Object.prototype.propertyIsEnumerable,
  Ge = function Ge(e, t, r) {
    return t in e ? hn(e, t, {
      enumerable: !0,
      configurable: !0,
      writable: !0,
      value: r
    }) : e[t] = r;
  },
  Et = function Et(e, t) {
    for (var r in t || (t = {})) wn.call(t, r) && Ge(e, r, t[r]);
    if (Ke) {
      var _iterator = _createForOfIteratorHelper(Ke(t)),
        _step;
      try {
        for (_iterator.s(); !(_step = _iterator.n()).done;) {
          var r = _step.value;
          bn.call(t, r) && Ge(e, r, t[r]);
        }
      } catch (err) {
        _iterator.e(err);
      } finally {
        _iterator.f();
      }
    }
    return e;
  },
  St = function St(e, t) {
    return An(e, yn(t));
  },
  xn = /^((?:background$)|devtools|popup|options|content-script|window)(?:@(\d+)(?:\.(\d+))?)?$/,
  Ot = function Ot(e) {
    var _ref20 = e.match(xn) || [],
      _ref21 = _slicedToArray(_ref20, 4),
      t = _ref21[1],
      r = _ref21[2],
      n = _ref21[3];
    return {
      context: t,
      tabId: +r,
      frameId: n ? +n : void 0
    };
  };
var En = [{
    property: "name",
    enumerable: !1
  }, {
    property: "message",
    enumerable: !1
  }, {
    property: "stack",
    enumerable: !1
  }, {
    property: "code",
    enumerable: !0
  }],
  Re = Symbol(".toJSON was called"),
  Sn = function Sn(e) {
    e[Re] = !0;
    var t = e.toJSON();
    return delete e[Re], t;
  },
  Rt = function Rt(_ref22) {
    var e = _ref22.from,
      t = _ref22.seen,
      r = _ref22.to_,
      n = _ref22.forceEnumerable,
      s = _ref22.maxDepth,
      i = _ref22.depth;
    var o = r || (Array.isArray(e) ? [] : {});
    if (t.push(e), i >= s) return o;
    if (typeof e.toJSON == "function" && e[Re] !== !0) return Sn(e);
    for (var _i2 = 0, _Object$entries = Object.entries(e); _i2 < _Object$entries.length; _i2++) {
      var _Object$entries$_i = _slicedToArray(_Object$entries[_i2], 2),
        a = _Object$entries$_i[0],
        u = _Object$entries$_i[1];
      if (typeof Buffer == "function" && Buffer.isBuffer(u)) {
        o[a] = "[object Buffer]";
        continue;
      }
      if (u !== null && _typeof(u) == "object" && typeof u.pipe == "function") {
        o[a] = "[object Stream]";
        continue;
      }
      if (typeof u != "function") {
        if (!u || _typeof(u) != "object") {
          o[a] = u;
          continue;
        }
        if (!t.includes(e[a])) {
          i++, o[a] = Rt({
            from: e[a],
            seen: _toConsumableArray(t),
            forceEnumerable: n,
            maxDepth: s,
            depth: i
          });
          continue;
        }
        o[a] = "[Circular]";
      }
    }
    for (var _i3 = 0, _En = En; _i3 < _En.length; _i3++) {
      var _En$_i = _En[_i3],
        _a = _En$_i.property,
        _u = _En$_i.enumerable;
      typeof e[_a] == "string" && Object.defineProperty(o, _a, {
        value: e[_a],
        enumerable: n ? !0 : _u,
        configurable: !0,
        writable: !0
      });
    }
    return o;
  };
function On(e) {
  var t = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};
  var _t$maxDepth = t.maxDepth,
    r = _t$maxDepth === void 0 ? Number.POSITIVE_INFINITY : _t$maxDepth;
  return _typeof(e) == "object" && e !== null ? Rt({
    from: e,
    seen: [],
    forceEnumerable: !0,
    maxDepth: r,
    depth: 0
  }) : typeof e == "function" ? "[Function: ".concat(e.name || "anonymous", "]") : e;
}
var Tt = function Tt() {
  return {
    events: {},
    emit: function emit(e) {
      for (var _len8 = arguments.length, t = new Array(_len8 > 1 ? _len8 - 1 : 0), _key8 = 1; _key8 < _len8; _key8++) {
        t[_key8 - 1] = arguments[_key8];
      }
      (this.events[e] || []).forEach(function (r) {
        return r.apply(void 0, t);
      });
    },
    on: function on(e, t) {
      var _this2 = this;
      return (this.events[e] = this.events[e] || []).push(t), function () {
        return _this2.events[e] = (_this2.events[e] || []).filter(function (r) {
          return r !== t;
        });
      };
    }
  };
};
var Rn = function Rn(e, t, r) {
    var n = re(),
      s = new Map(),
      i = new Map(),
      o = function o(a) {
        if (a.destination.context === e && !a.destination.frameId && !a.destination.tabId) {
          r == null || r(a);
          var u = a.transactionId,
            c = a.messageID,
            f = a.messageType,
            m = function m() {
              var A = s.get(u);
              if (A) {
                var d = a.err,
                  h = a.data;
                if (d) {
                  var S = d,
                    C = self[S.name],
                    N = new (typeof C == "function" ? C : Error)(S.message);
                  for (var I in S) N[I] = S[I];
                  A.reject(N);
                } else A.resolve(h);
                s.delete(u);
              }
            },
            y = /*#__PURE__*/function () {
              var _ref23 = _asyncToGenerator( /*#__PURE__*/_regeneratorRuntime().mark(function _callee9() {
                var A, d, h, S;
                return _regeneratorRuntime().wrap(function _callee9$(_context9) {
                  while (1) switch (_context9.prev = _context9.next) {
                    case 0:
                      h = !1;
                      _context9.prev = 1;
                      S = i.get(c);
                      if (!(typeof S == "function")) {
                        _context9.next = 9;
                        break;
                      }
                      _context9.next = 6;
                      return S({
                        sender: a.origin,
                        id: c,
                        data: a.data,
                        timestamp: a.timestamp
                      });
                    case 6:
                      A = _context9.sent;
                      _context9.next = 10;
                      break;
                    case 9:
                      throw h = !0, new Error("[webext-bridge] No handler registered in '".concat(e, "' to accept messages with id '").concat(c, "'"));
                    case 10:
                      _context9.next = 15;
                      break;
                    case 12:
                      _context9.prev = 12;
                      _context9.t0 = _context9["catch"](1);
                      d = _context9.t0;
                    case 15:
                      _context9.prev = 15;
                      if (!(d && (a.err = On(d)), o(St(Et({}, a), {
                        messageType: "reply",
                        data: A,
                        origin: {
                          context: e,
                          tabId: null
                        },
                        destination: a.origin,
                        hops: []
                      })), d && !h)) {
                        _context9.next = 18;
                        break;
                      }
                      throw A;
                    case 18:
                      return _context9.finish(15);
                    case 19:
                    case "end":
                      return _context9.stop();
                  }
                }, _callee9, null, [[1, 12, 15, 19]]);
              }));
              return function y() {
                return _ref23.apply(this, arguments);
              };
            }();
          switch (f) {
            case "reply":
              return m();
            case "message":
              return y();
          }
        }
        return a.hops.push("".concat(e, "::").concat(n)), t(a);
      };
    return {
      handleMessage: o,
      endTransaction: function endTransaction(a) {
        var u = s.get(a);
        u == null || u.reject("Transaction was ended before it could complete"), s.delete(a);
      },
      sendMessage: function sendMessage(a, u) {
        var c = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : "background";
        var f = typeof c == "string" ? Ot(c) : c,
          m = "Bridge#sendMessage ->";
        if (!f.context) throw new TypeError("".concat(m, " Destination must be any one of known destinations"));
        return new Promise(function (y, A) {
          var d = {
            messageID: a,
            data: u,
            destination: f,
            messageType: "message",
            transactionId: re(),
            origin: {
              context: e,
              tabId: null
            },
            hops: [],
            timestamp: Date.now()
          };
          s.set(d.transactionId, {
            resolve: y,
            reject: A
          });
          try {
            o(d);
          } catch (h) {
            s.delete(d.transactionId), A(h);
          }
        });
      },
      onMessage: function onMessage(a, u) {
        return i.set(a, u), function () {
          return i.delete(a);
        };
      }
    };
  },
  $ = /*#__PURE__*/function () {
    function $(e, t) {
      var _this3 = this;
      _classCallCheck(this, $);
      this.endpointRuntime = e, this.streamInfo = t, this.emitter = Tt(), this.isClosed = !1, this.handleStreamClose = function () {
        _this3.isClosed || (_this3.isClosed = !0, _this3.emitter.emit("closed", !0), _this3.emitter.events = {});
      }, $.initDone || (e.onMessage("__crx_bridge_stream_transfer__", function (r) {
        var _r$data = r.data,
          n = _r$data.streamId,
          s = _r$data.streamTransfer,
          i = _r$data.action,
          o = $.openStreams.get(n);
        o && !o.isClosed && (i === "transfer" && o.emitter.emit("message", s), i === "close" && ($.openStreams.delete(n), o.handleStreamClose()));
      }), $.initDone = !0), $.openStreams.set(this.streamInfo.streamId, this);
    }
    _createClass($, [{
      key: "info",
      get: function get() {
        return this.streamInfo;
      }
    }, {
      key: "send",
      value: function send(e) {
        if (this.isClosed) throw new Error("Attempting to send a message over closed stream. Use stream.onClose(<callback>) to keep an eye on stream status");
        this.endpointRuntime.sendMessage("__crx_bridge_stream_transfer__", {
          streamId: this.streamInfo.streamId,
          streamTransfer: e,
          action: "transfer"
        }, this.streamInfo.endpoint);
      }
    }, {
      key: "close",
      value: function close(e) {
        e && this.send(e), this.handleStreamClose(), this.endpointRuntime.sendMessage("__crx_bridge_stream_transfer__", {
          streamId: this.streamInfo.streamId,
          streamTransfer: null,
          action: "close"
        }, this.streamInfo.endpoint);
      }
    }, {
      key: "onMessage",
      value: function onMessage(e) {
        return this.getDisposable("message", e);
      }
    }, {
      key: "onClose",
      value: function onClose(e) {
        return this.getDisposable("closed", e);
      }
    }, {
      key: "getDisposable",
      value: function getDisposable(e, t) {
        var r = this.emitter.on(e, t);
        return Object.assign(r, {
          dispose: r,
          close: r
        });
      }
    }]);
    return $;
  }(),
  ne = $;
ne.initDone = !1;
ne.openStreams = new Map();
var Tn = function Tn(e) {
    var t = new Map(),
      r = new Map(),
      n = Tt();
    e.onMessage("__crx_bridge_stream_open__", function (o) {
      return new Promise(function (a) {
        var u = o.sender,
          c = o.data,
          f = c.channel;
        var m = !1,
          y = function y() {};
        var A = function A() {
          var d = r.get(f);
          typeof d == "function" ? (d(new ne(e, St(Et({}, c), {
            endpoint: u
          }))), m && y(), a(!0)) : m || (m = !0, y = n.on("did-change-stream-callbacks", A));
        };
        A();
      });
    });
    function s(_x9, _x10) {
      return _s2.apply(this, arguments);
    }
    function _s2() {
      _s2 = _asyncToGenerator( /*#__PURE__*/_regeneratorRuntime().mark(function _callee10(o, a) {
        var u, c, f;
        return _regeneratorRuntime().wrap(function _callee10$(_context10) {
          while (1) switch (_context10.prev = _context10.next) {
            case 0:
              if (!t.has(o)) {
                _context10.next = 2;
                break;
              }
              throw new Error("webext-bridge: A Stream is already open at this channel");
            case 2:
              u = typeof a == "string" ? Ot(a) : a, c = {
                streamId: re(),
                channel: o,
                endpoint: u
              }, f = new ne(e, c);
              f.onClose(function () {
                return t.delete(o);
              });
              _context10.next = 6;
              return e.sendMessage("__crx_bridge_stream_open__", c, u);
            case 6:
              t.set(o, f);
              return _context10.abrupt("return", f);
            case 8:
            case "end":
              return _context10.stop();
          }
        }, _callee10);
      }));
      return _s2.apply(this, arguments);
    }
    function i(o, a) {
      if (r.has(o)) throw new Error("webext-bridge: This channel has already been claimed. Stream allows only one-on-one communication");
      r.set(o, a), n.emit("did-change-stream-callbacks");
    }
    return {
      openStream: s,
      onOpenStreamChannel: i
    };
  },
  ve = gn("content-script"),
  Ie = dn(),
  X = Rn("content-script", function (e) {
    e.destination.context === "window" ? ve.postMessage(e) : Ie.postMessage(e);
  });
ve.onMessage(function (e) {
  e.origin = {
    context: "window",
    tabId: null
  }, X.handleMessage(e);
});
Ie.onMessage(X.handleMessage);
Ie.onFailure(function (e) {
  if (e.origin.context === "window") {
    ve.postMessage({
      type: "error",
      transactionID: e.transactionId
    });
    return;
  }
  X.endTransaction(e.transactionId);
});
var In = X.sendMessage,
  Fn = X.onMessage;
Tn(X);
export { _n as a, vn as b, Qr as g, Mn as r, In as s };
