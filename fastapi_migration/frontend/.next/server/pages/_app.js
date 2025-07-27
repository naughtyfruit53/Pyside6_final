"use strict";
/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
(() => {
var exports = {};
exports.id = "pages/_app";
exports.ids = ["pages/_app"];
exports.modules = {

/***/ "./src/pages/_app.tsx":
/*!****************************!*\
  !*** ./src/pages/_app.tsx ***!
  \****************************/
/***/ ((module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.a(module, async (__webpack_handle_async_dependencies__, __webpack_async_result__) => { try {\n__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"default\": () => (__WEBPACK_DEFAULT_EXPORT__)\n/* harmony export */ });\n/* harmony import */ var react_jsx_dev_runtime__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! react/jsx-dev-runtime */ \"react/jsx-dev-runtime\");\n/* harmony import */ var react_jsx_dev_runtime__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react_jsx_dev_runtime__WEBPACK_IMPORTED_MODULE_0__);\n/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! react */ \"react\");\n/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_1__);\n/* harmony import */ var _mui_material_styles__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @mui/material/styles */ \"@mui/material/styles\");\n/* harmony import */ var _mui_material_styles__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_mui_material_styles__WEBPACK_IMPORTED_MODULE_2__);\n/* harmony import */ var _mui_material_CssBaseline__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @mui/material/CssBaseline */ \"@mui/material/CssBaseline\");\n/* harmony import */ var _mui_material_CssBaseline__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(_mui_material_CssBaseline__WEBPACK_IMPORTED_MODULE_3__);\n/* harmony import */ var react_query__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! react-query */ \"react-query\");\n/* harmony import */ var react_query__WEBPACK_IMPORTED_MODULE_4___default = /*#__PURE__*/__webpack_require__.n(react_query__WEBPACK_IMPORTED_MODULE_4__);\n/* harmony import */ var react_toastify__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! react-toastify */ \"react-toastify\");\n/* harmony import */ var react_toastify_dist_ReactToastify_css__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! react-toastify/dist/ReactToastify.css */ \"./node_modules/react-toastify/dist/ReactToastify.css\");\n/* harmony import */ var react_toastify_dist_ReactToastify_css__WEBPACK_IMPORTED_MODULE_6___default = /*#__PURE__*/__webpack_require__.n(react_toastify_dist_ReactToastify_css__WEBPACK_IMPORTED_MODULE_6__);\nvar __webpack_async_dependencies__ = __webpack_handle_async_dependencies__([react_toastify__WEBPACK_IMPORTED_MODULE_5__]);\nreact_toastify__WEBPACK_IMPORTED_MODULE_5__ = (__webpack_async_dependencies__.then ? (await __webpack_async_dependencies__)() : __webpack_async_dependencies__)[0];\n\n\n\n\n\n\n\n// Create theme\nconst theme = (0,_mui_material_styles__WEBPACK_IMPORTED_MODULE_2__.createTheme)({\n    palette: {\n        primary: {\n            main: \"#0D47A1\"\n        },\n        secondary: {\n            main: \"#1976D2\"\n        }\n    },\n    typography: {\n        fontFamily: '\"Roboto\", \"Helvetica\", \"Arial\", sans-serif'\n    }\n});\n// Create query client\nconst queryClient = new react_query__WEBPACK_IMPORTED_MODULE_4__.QueryClient({\n    defaultOptions: {\n        queries: {\n            retry: 1,\n            refetchOnWindowFocus: false\n        }\n    }\n});\nfunction MyApp({ Component, pageProps }) {\n    return /*#__PURE__*/ (0,react_jsx_dev_runtime__WEBPACK_IMPORTED_MODULE_0__.jsxDEV)(react_query__WEBPACK_IMPORTED_MODULE_4__.QueryClientProvider, {\n        client: queryClient,\n        children: /*#__PURE__*/ (0,react_jsx_dev_runtime__WEBPACK_IMPORTED_MODULE_0__.jsxDEV)(_mui_material_styles__WEBPACK_IMPORTED_MODULE_2__.ThemeProvider, {\n            theme: theme,\n            children: [\n                /*#__PURE__*/ (0,react_jsx_dev_runtime__WEBPACK_IMPORTED_MODULE_0__.jsxDEV)((_mui_material_CssBaseline__WEBPACK_IMPORTED_MODULE_3___default()), {}, void 0, false, {\n                    fileName: \"D:\\\\Tri_rev\\\\Pyside6_final\\\\fastapi_migration\\\\frontend\\\\src\\\\pages\\\\_app.tsx\",\n                    lineNumber: 38,\n                    columnNumber: 9\n                }, this),\n                /*#__PURE__*/ (0,react_jsx_dev_runtime__WEBPACK_IMPORTED_MODULE_0__.jsxDEV)(Component, {\n                    ...pageProps\n                }, void 0, false, {\n                    fileName: \"D:\\\\Tri_rev\\\\Pyside6_final\\\\fastapi_migration\\\\frontend\\\\src\\\\pages\\\\_app.tsx\",\n                    lineNumber: 39,\n                    columnNumber: 9\n                }, this),\n                /*#__PURE__*/ (0,react_jsx_dev_runtime__WEBPACK_IMPORTED_MODULE_0__.jsxDEV)(react_toastify__WEBPACK_IMPORTED_MODULE_5__.ToastContainer, {\n                    position: \"top-right\",\n                    autoClose: 5000,\n                    hideProgressBar: false,\n                    newestOnTop: false,\n                    closeOnClick: true,\n                    rtl: false,\n                    pauseOnFocusLoss: true,\n                    draggable: true,\n                    pauseOnHover: true\n                }, void 0, false, {\n                    fileName: \"D:\\\\Tri_rev\\\\Pyside6_final\\\\fastapi_migration\\\\frontend\\\\src\\\\pages\\\\_app.tsx\",\n                    lineNumber: 40,\n                    columnNumber: 9\n                }, this)\n            ]\n        }, void 0, true, {\n            fileName: \"D:\\\\Tri_rev\\\\Pyside6_final\\\\fastapi_migration\\\\frontend\\\\src\\\\pages\\\\_app.tsx\",\n            lineNumber: 37,\n            columnNumber: 7\n        }, this)\n    }, void 0, false, {\n        fileName: \"D:\\\\Tri_rev\\\\Pyside6_final\\\\fastapi_migration\\\\frontend\\\\src\\\\pages\\\\_app.tsx\",\n        lineNumber: 36,\n        columnNumber: 5\n    }, this);\n}\n/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (MyApp);\n\n__webpack_async_result__();\n} catch(e) { __webpack_async_result__(e); } });//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiLi9zcmMvcGFnZXMvX2FwcC50c3giLCJtYXBwaW5ncyI6Ijs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7O0FBQTBCO0FBRXdDO0FBQ2Q7QUFDVztBQUNmO0FBQ0Q7QUFFL0MsZUFBZTtBQUNmLE1BQU1PLFFBQVFMLGlFQUFXQSxDQUFDO0lBQ3hCTSxTQUFTO1FBQ1BDLFNBQVM7WUFDUEMsTUFBTTtRQUNSO1FBQ0FDLFdBQVc7WUFDVEQsTUFBTTtRQUNSO0lBQ0Y7SUFDQUUsWUFBWTtRQUNWQyxZQUFZO0lBQ2Q7QUFDRjtBQUVBLHNCQUFzQjtBQUN0QixNQUFNQyxjQUFjLElBQUlWLG9EQUFXQSxDQUFDO0lBQ2xDVyxnQkFBZ0I7UUFDZEMsU0FBUztZQUNQQyxPQUFPO1lBQ1BDLHNCQUFzQjtRQUN4QjtJQUNGO0FBQ0Y7QUFFQSxTQUFTQyxNQUFNLEVBQUVDLFNBQVMsRUFBRUMsU0FBUyxFQUFZO0lBQy9DLHFCQUNFLDhEQUFDaEIsNERBQW1CQTtRQUFDaUIsUUFBUVI7a0JBQzNCLDRFQUFDYiwrREFBYUE7WUFBQ00sT0FBT0E7OzhCQUNwQiw4REFBQ0osa0VBQVdBOzs7Ozs4QkFDWiw4REFBQ2lCO29CQUFXLEdBQUdDLFNBQVM7Ozs7Ozs4QkFDeEIsOERBQUNmLDBEQUFjQTtvQkFDYmlCLFVBQVM7b0JBQ1RDLFdBQVc7b0JBQ1hDLGlCQUFpQjtvQkFDakJDLGFBQWE7b0JBQ2JDLFlBQVk7b0JBQ1pDLEtBQUs7b0JBQ0xDLGdCQUFnQjtvQkFDaEJDLFNBQVM7b0JBQ1RDLFlBQVk7Ozs7Ozs7Ozs7Ozs7Ozs7O0FBS3RCO0FBRUEsaUVBQWVaLEtBQUtBLEVBQUMiLCJzb3VyY2VzIjpbIndlYnBhY2s6Ly90cml0aXEtZXJwLWZyb250ZW5kLy4vc3JjL3BhZ2VzL19hcHAudHN4P2Y5ZDYiXSwic291cmNlc0NvbnRlbnQiOlsiaW1wb3J0IFJlYWN0IGZyb20gJ3JlYWN0JztcclxuaW1wb3J0IHsgQXBwUHJvcHMgfSBmcm9tICduZXh0L2FwcCc7XHJcbmltcG9ydCB7IFRoZW1lUHJvdmlkZXIsIGNyZWF0ZVRoZW1lIH0gZnJvbSAnQG11aS9tYXRlcmlhbC9zdHlsZXMnO1xyXG5pbXBvcnQgQ3NzQmFzZWxpbmUgZnJvbSAnQG11aS9tYXRlcmlhbC9Dc3NCYXNlbGluZSc7XHJcbmltcG9ydCB7IFF1ZXJ5Q2xpZW50LCBRdWVyeUNsaWVudFByb3ZpZGVyIH0gZnJvbSAncmVhY3QtcXVlcnknO1xyXG5pbXBvcnQgeyBUb2FzdENvbnRhaW5lciB9IGZyb20gJ3JlYWN0LXRvYXN0aWZ5JztcclxuaW1wb3J0ICdyZWFjdC10b2FzdGlmeS9kaXN0L1JlYWN0VG9hc3RpZnkuY3NzJztcclxuXHJcbi8vIENyZWF0ZSB0aGVtZVxyXG5jb25zdCB0aGVtZSA9IGNyZWF0ZVRoZW1lKHtcclxuICBwYWxldHRlOiB7XHJcbiAgICBwcmltYXJ5OiB7XHJcbiAgICAgIG1haW46ICcjMEQ0N0ExJyxcclxuICAgIH0sXHJcbiAgICBzZWNvbmRhcnk6IHtcclxuICAgICAgbWFpbjogJyMxOTc2RDInLFxyXG4gICAgfSxcclxuICB9LFxyXG4gIHR5cG9ncmFwaHk6IHtcclxuICAgIGZvbnRGYW1pbHk6ICdcIlJvYm90b1wiLCBcIkhlbHZldGljYVwiLCBcIkFyaWFsXCIsIHNhbnMtc2VyaWYnLFxyXG4gIH0sXHJcbn0pO1xyXG5cclxuLy8gQ3JlYXRlIHF1ZXJ5IGNsaWVudFxyXG5jb25zdCBxdWVyeUNsaWVudCA9IG5ldyBRdWVyeUNsaWVudCh7XHJcbiAgZGVmYXVsdE9wdGlvbnM6IHtcclxuICAgIHF1ZXJpZXM6IHtcclxuICAgICAgcmV0cnk6IDEsXHJcbiAgICAgIHJlZmV0Y2hPbldpbmRvd0ZvY3VzOiBmYWxzZSxcclxuICAgIH0sXHJcbiAgfSxcclxufSk7XHJcblxyXG5mdW5jdGlvbiBNeUFwcCh7IENvbXBvbmVudCwgcGFnZVByb3BzIH06IEFwcFByb3BzKSB7XHJcbiAgcmV0dXJuIChcclxuICAgIDxRdWVyeUNsaWVudFByb3ZpZGVyIGNsaWVudD17cXVlcnlDbGllbnR9PlxyXG4gICAgICA8VGhlbWVQcm92aWRlciB0aGVtZT17dGhlbWV9PlxyXG4gICAgICAgIDxDc3NCYXNlbGluZSAvPlxyXG4gICAgICAgIDxDb21wb25lbnQgey4uLnBhZ2VQcm9wc30gLz5cclxuICAgICAgICA8VG9hc3RDb250YWluZXJcclxuICAgICAgICAgIHBvc2l0aW9uPVwidG9wLXJpZ2h0XCJcclxuICAgICAgICAgIGF1dG9DbG9zZT17NTAwMH1cclxuICAgICAgICAgIGhpZGVQcm9ncmVzc0Jhcj17ZmFsc2V9XHJcbiAgICAgICAgICBuZXdlc3RPblRvcD17ZmFsc2V9XHJcbiAgICAgICAgICBjbG9zZU9uQ2xpY2tcclxuICAgICAgICAgIHJ0bD17ZmFsc2V9XHJcbiAgICAgICAgICBwYXVzZU9uRm9jdXNMb3NzXHJcbiAgICAgICAgICBkcmFnZ2FibGVcclxuICAgICAgICAgIHBhdXNlT25Ib3ZlclxyXG4gICAgICAgIC8+XHJcbiAgICAgIDwvVGhlbWVQcm92aWRlcj5cclxuICAgIDwvUXVlcnlDbGllbnRQcm92aWRlcj5cclxuICApO1xyXG59XHJcblxyXG5leHBvcnQgZGVmYXVsdCBNeUFwcDsiXSwibmFtZXMiOlsiUmVhY3QiLCJUaGVtZVByb3ZpZGVyIiwiY3JlYXRlVGhlbWUiLCJDc3NCYXNlbGluZSIsIlF1ZXJ5Q2xpZW50IiwiUXVlcnlDbGllbnRQcm92aWRlciIsIlRvYXN0Q29udGFpbmVyIiwidGhlbWUiLCJwYWxldHRlIiwicHJpbWFyeSIsIm1haW4iLCJzZWNvbmRhcnkiLCJ0eXBvZ3JhcGh5IiwiZm9udEZhbWlseSIsInF1ZXJ5Q2xpZW50IiwiZGVmYXVsdE9wdGlvbnMiLCJxdWVyaWVzIiwicmV0cnkiLCJyZWZldGNoT25XaW5kb3dGb2N1cyIsIk15QXBwIiwiQ29tcG9uZW50IiwicGFnZVByb3BzIiwiY2xpZW50IiwicG9zaXRpb24iLCJhdXRvQ2xvc2UiLCJoaWRlUHJvZ3Jlc3NCYXIiLCJuZXdlc3RPblRvcCIsImNsb3NlT25DbGljayIsInJ0bCIsInBhdXNlT25Gb2N1c0xvc3MiLCJkcmFnZ2FibGUiLCJwYXVzZU9uSG92ZXIiXSwic291cmNlUm9vdCI6IiJ9\n//# sourceURL=webpack-internal:///./src/pages/_app.tsx\n");

/***/ }),

/***/ "@mui/material/CssBaseline":
/*!********************************************!*\
  !*** external "@mui/material/CssBaseline" ***!
  \********************************************/
/***/ ((module) => {

module.exports = require("@mui/material/CssBaseline");

/***/ }),

/***/ "@mui/material/styles":
/*!***************************************!*\
  !*** external "@mui/material/styles" ***!
  \***************************************/
/***/ ((module) => {

module.exports = require("@mui/material/styles");

/***/ }),

/***/ "react":
/*!************************!*\
  !*** external "react" ***!
  \************************/
/***/ ((module) => {

module.exports = require("react");

/***/ }),

/***/ "react-query":
/*!******************************!*\
  !*** external "react-query" ***!
  \******************************/
/***/ ((module) => {

module.exports = require("react-query");

/***/ }),

/***/ "react/jsx-dev-runtime":
/*!****************************************!*\
  !*** external "react/jsx-dev-runtime" ***!
  \****************************************/
/***/ ((module) => {

module.exports = require("react/jsx-dev-runtime");

/***/ }),

/***/ "react-toastify":
/*!*********************************!*\
  !*** external "react-toastify" ***!
  \*********************************/
/***/ ((module) => {

module.exports = import("react-toastify");;

/***/ })

};
;

// load runtime
var __webpack_require__ = require("../webpack-runtime.js");
__webpack_require__.C(exports);
var __webpack_exec__ = (moduleId) => (__webpack_require__(__webpack_require__.s = moduleId))
var __webpack_exports__ = __webpack_require__.X(0, ["vendor-chunks/react-toastify"], () => (__webpack_exec__("./src/pages/_app.tsx")));
module.exports = __webpack_exports__;

})();