const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("verttrade", {
  appName: "VertTrade",
});
