import { app } from "../../scripts/app.js";

/*
 * FloorPlan Camera Node — Interactive 2D Canvas
 * v1.2 — Canvas below widgets, image in canvas, no auto-preview
 */

const CANVAS_H = 380;
const CAM_R = 12;
const FOV_DEG = 70;
const FOV_LEN = 65;
const HANDLE_R = 7;
const C = {
    bg: "#111114",
    border: "#444",
    cam: "#4ade80",
    camDk: "#166534",
    fovFill: "rgba(74, 222, 128, 0.18)",
    fovLine: "rgba(74, 222, 128, 0.6)",
    handle: "#facc15",
    handleS: "#fef9c3",
    label: "#4ade80",
    labelBg: "rgba(0,0,0,0.75)",
    ph: "#666",
    grid: "rgba(255,255,255,0.04)",
};

app.registerExtension({
    name: "FloorPlan.CameraNode",

    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        if (nodeData.name !== "FloorPlanCameraNode") return;

        // ── Init ──
        const origCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            origCreated?.apply(this, arguments);
            this._fp = {
                cx: 0.5, cy: 0.5, rot: 0,
                img: null, loaded: false,
                drag: false, spin: false,
                rect: null, hndl: null,
            };
            this.size = [480, 600];
            requestAnimationFrame(() => this._fpHide());
        };

        // ── Hide cam widgets ──
        nodeType.prototype._fpHide = function () {
            for (const w of this.widgets || []) {
                if (["cam_x", "cam_y", "cam_rotation"].includes(w.name) ||
                    w.name === "image" || w.type === "image" || w.name === "preview") {
                    w.computeSize = () => [0, -4];
                    w.type = "converted-widget";
                }
            }
        };

        // ── Sync to Python ──
        nodeType.prototype._fpSync = function () {
            for (const w of this.widgets || []) {
                if (w.name === "cam_x") w.value = this._fp.cx;
                if (w.name === "cam_y") w.value = this._fp.cy;
                if (w.name === "cam_rotation") w.value = this._fp.rot;
            }
        };

        // ── Get Y where widgets end ──
        nodeType.prototype._fpWidgetEndY = function () {
            let maxY = 30; // title bar height
            for (const w of this.widgets || []) {
                if (w.type === "converted-widget") continue;
                if (w.last_y !== undefined && w.last_y !== null) {
                    const wh = w.computedHeight || 22;
                    maxY = Math.max(maxY, w.last_y + wh + 4);
                }
            }
            // Fallback: count visible widgets
            if (maxY <= 34) {
                let visible = 0;
                for (const w of this.widgets || []) {
                    if (w.type !== "converted-widget") visible++;
                }
                maxY = 30 + visible * 26 + 8;
            }
            return maxY;
        };

        // ── Restore from saved workflow ──
        const origCfg = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            origCfg?.apply(this, arguments);
            requestAnimationFrame(() => this._fpHide());
            for (const w of this.widgets || []) {
                if (w.name === "cam_x") this._fp.cx = w.value ?? 0.5;
                if (w.name === "cam_y") this._fp.cy = w.value ?? 0.5;
                if (w.name === "cam_rotation") this._fp.rot = w.value ?? 0;
            }
        };

        // ── Load image helper ──
        nodeType.prototype._fpLoad = function (url) {
            const self = this;
            const im = new Image();
            im.crossOrigin = "anonymous";
            im.onload = () => {
                self._fp.img = im;
                self._fp.loaded = true;
                self.imgs = null;
                self._fpHide();
                self.setDirtyCanvas(true, true);
            };
            im.src = url;
        };

        // ── After execution: load preview into canvas ──
        const origExec = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (msg) {
            origExec?.apply(this, arguments);
            if (msg?.images?.[0]) {
                const im = msg.images[0];
                this._fpLoad(`/view?filename=${encodeURIComponent(im.filename)}&type=${im.type}&subfolder=${encodeURIComponent(im.subfolder || "")}`);
            }
            requestAnimationFrame(() => {
                this.imgs = null;
                this._fpHide();
                this.setDirtyCanvas(true, true);
            });
        };

        // ── On connect: try loading from upstream ──
        const origConn = nodeType.prototype.onConnectionsChange;
        nodeType.prototype.onConnectionsChange = function (side, slot, conn, link) {
            origConn?.apply(this, arguments);
            if (side === 1 && slot === 0 && conn && link) {
                try {
                    const src = app.graph.getNodeById(link.origin_id);
                    if (src?.imgs?.[0]?.src) {
                        this._fpLoad(src.imgs[0].src);
                        return;
                    }
                    if (src?.widgets) {
                        for (const w of src.widgets) {
                            if (w.name === "image" && w.value) {
                                this._fpLoad(`/view?filename=${encodeURIComponent(w.value)}&type=input`);
                                return;
                            }
                        }
                    }
                } catch (e) { /* onExecuted fallback */ }
            }
        };

        // ── Kill auto-preview ──
        nodeType.prototype.onDrawBackground = function () {
            if (this.imgs) this.imgs = null;
        };

        // ── Main draw ──
        const origDraw = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function (ctx) {
            origDraw?.apply(this, arguments);
            if (this.flags?.collapsed) return;

            const pad = 8;
            const topY = this._fpWidgetEndY() + 6;
            const cw = this.size[0] - pad * 2;
            const ch = CANVAS_H;

            // Auto-resize node height to fit canvas
            const needed = topY + ch + 12;
            if (this.size[1] < needed) {
                this.size[1] = needed;
            }

            this._fp.rect = { x: pad, y: topY, w: cw, h: ch };

            // ── BG ──
            ctx.fillStyle = C.bg;
            ctx.fillRect(pad, topY, cw, ch);

            // ── Grid ──
            ctx.strokeStyle = C.grid;
            ctx.lineWidth = 0.5;
            for (let gx = pad + 30; gx < pad + cw; gx += 30) {
                ctx.beginPath(); ctx.moveTo(gx, topY); ctx.lineTo(gx, topY + ch); ctx.stroke();
            }
            for (let gy = topY + 30; gy < topY + ch; gy += 30) {
                ctx.beginPath(); ctx.moveTo(pad, gy); ctx.lineTo(pad + cw, gy); ctx.stroke();
            }

            // ── Floor plan image ──
            if (this._fp.img && this._fp.loaded && this._fp.img.naturalWidth > 0) {
                const ia = this._fp.img.naturalWidth / this._fp.img.naturalHeight;
                const ca = cw / ch;
                let dw, dh, dx, dy;
                if (ia > ca) {
                    dw = cw; dh = cw / ia; dx = pad; dy = topY + (ch - dh) / 2;
                } else {
                    dh = ch; dw = ch * ia; dx = pad + (cw - dw) / 2; dy = topY;
                }
                ctx.globalAlpha = 0.9;
                ctx.drawImage(this._fp.img, dx, dy, dw, dh);
                ctx.globalAlpha = 1.0;
            } else {
                ctx.fillStyle = C.ph;
                ctx.font = "14px sans-serif";
                ctx.textAlign = "center";
                ctx.fillText("Connect image_plan & Queue Prompt", pad + cw / 2, topY + ch / 2 - 8);
                ctx.font = "12px sans-serif";
                ctx.fillText("Floor plan will appear here", pad + cw / 2, topY + ch / 2 + 14);
                ctx.textAlign = "left";
            }

            // ── Border ──
            ctx.strokeStyle = C.border;
            ctx.lineWidth = 1.5;
            ctx.strokeRect(pad, topY, cw, ch);

            // ── Camera ──
            const cx = pad + this._fp.cx * cw;
            const cy = topY + this._fp.cy * ch;
            const rr = (this._fp.rot - 90) * Math.PI / 180;
            const hf = (FOV_DEG / 2) * Math.PI / 180;

            // FOV cone
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.lineTo(cx + Math.cos(rr - hf) * FOV_LEN, cy + Math.sin(rr - hf) * FOV_LEN);
            ctx.arc(cx, cy, FOV_LEN, rr - hf, rr + hf);
            ctx.closePath();
            ctx.fillStyle = C.fovFill;
            ctx.fill();
            ctx.strokeStyle = C.fovLine;
            ctx.lineWidth = 1;
            ctx.stroke();

            // Direction line
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.lineTo(cx + Math.cos(rr) * (FOV_LEN + 5), cy + Math.sin(rr) * (FOV_LEN + 5));
            ctx.strokeStyle = C.cam;
            ctx.lineWidth = 1.5;
            ctx.setLineDash([4, 3]);
            ctx.stroke();
            ctx.setLineDash([]);

            // Camera circle
            ctx.save();
            ctx.translate(cx, cy);
            ctx.beginPath();
            ctx.arc(0, 0, CAM_R, 0, Math.PI * 2);
            ctx.fillStyle = C.camDk;
            ctx.fill();
            ctx.strokeStyle = C.cam;
            ctx.lineWidth = 2;
            ctx.stroke();
            ctx.beginPath();
            ctx.arc(0, 0, 3, 0, Math.PI * 2);
            ctx.fillStyle = C.cam;
            ctx.fill();
            ctx.rotate(rr);
            ctx.beginPath();
            ctx.moveTo(CAM_R - 3, 0);
            ctx.lineTo(CAM_R + 4, 0);
            ctx.strokeStyle = C.cam;
            ctx.lineWidth = 2.5;
            ctx.stroke();
            ctx.restore();

            // Rotation handle
            const hd = FOV_LEN + 15;
            const hx = cx + Math.cos(rr) * hd;
            const hy = cy + Math.sin(rr) * hd;
            ctx.beginPath();
            ctx.arc(hx, hy, HANDLE_R, 0, Math.PI * 2);
            ctx.fillStyle = C.handle;
            ctx.fill();
            ctx.strokeStyle = C.handleS;
            ctx.lineWidth = 1.5;
            ctx.stroke();
            ctx.beginPath();
            ctx.arc(hx, hy, 3.5, 0, Math.PI * 1.5);
            ctx.strokeStyle = "#78350f";
            ctx.lineWidth = 1.5;
            ctx.stroke();
            this._fp.hndl = { x: hx, y: hy };

            // Info bar
            ctx.fillStyle = C.labelBg;
            ctx.fillRect(pad, topY + ch - 22, cw, 22);
            ctx.fillStyle = C.label;
            ctx.font = "bold 11px monospace";
            ctx.textAlign = "left";
            const dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
            const card = dirs[Math.round(((this._fp.rot % 360) + 360) % 360 / 45) % 8];
            ctx.fillText(
                `X:${(this._fp.cx * 100).toFixed(0)}%  Y:${(this._fp.cy * 100).toFixed(0)}%   ${this._fp.rot.toFixed(1)}° ${card}`,
                pad + 8, topY + ch - 7
            );
        };

        // ── Mouse Down ──
        const origMD = nodeType.prototype.onMouseDown;
        nodeType.prototype.onMouseDown = function (e, pos) {
            const r = this._fp?.rect;
            if (!r) return origMD?.apply(this, arguments) ?? false;
            const [mx, my] = pos;

            if (mx < r.x || mx > r.x + r.w || my < r.y || my > r.y + r.h)
                return origMD?.apply(this, arguments) ?? false;

            // Rotation handle
            if (this._fp.hndl) {
                const dx = mx - this._fp.hndl.x, dy = my - this._fp.hndl.y;
                if (dx * dx + dy * dy < (HANDLE_R + 6) ** 2) {
                    this._fp.spin = true;
                    return true;
                }
            }
            // Camera
            const ax = r.x + this._fp.cx * r.w, ay = r.y + this._fp.cy * r.h;
            const dx = mx - ax, dy = my - ay;
            if (dx * dx + dy * dy < (CAM_R + 5) ** 2) {
                this._fp.drag = true;
                return true;
            }
            // Click → teleport
            this._fp.cx = Math.max(0, Math.min(1, (mx - r.x) / r.w));
            this._fp.cy = Math.max(0, Math.min(1, (my - r.y) / r.h));
            this._fp.drag = true;
            this._fpSync();
            this.setDirtyCanvas(true, true);
            return true;
        };

        // ── Mouse Move ──
        const origMM = nodeType.prototype.onMouseMove;
        nodeType.prototype.onMouseMove = function (e, pos) {
            const r = this._fp?.rect;
            if (!r) return origMM?.apply(this, arguments) ?? false;
            const [mx, my] = pos;

            if (this._fp.drag) {
                this._fp.cx = Math.max(0, Math.min(1, (mx - r.x) / r.w));
                this._fp.cy = Math.max(0, Math.min(1, (my - r.y) / r.h));
                this._fpSync();
                this.setDirtyCanvas(true, true);
                return true;
            }
            if (this._fp.spin) {
                const ax = r.x + this._fp.cx * r.w, ay = r.y + this._fp.cy * r.h;
                const a = Math.atan2(my - ay, mx - ax);
                this._fp.rot = ((a * 180 / Math.PI) + 90 + 360) % 360;
                this._fpSync();
                this.setDirtyCanvas(true, true);
                return true;
            }
            return origMM?.apply(this, arguments) ?? false;
        };

        // ── Mouse Up ──
        const origMU = nodeType.prototype.onMouseUp;
        nodeType.prototype.onMouseUp = function (e, pos) {
            if (this._fp?.drag || this._fp?.spin) {
                this._fp.drag = false;
                this._fp.spin = false;
                return true;
            }
            return origMU?.apply(this, arguments) ?? false;
        };
    },

    async nodeCreated(node) {
        if (node.comfyClass === "MaterialRefNode") {
            node.color = "#1a3a2a";
            node.bgcolor = "#0d1f15";
        }
        if (node.comfyClass === "FloorPlanCameraNode") {
            node.color = "#1a2a3a";
            node.bgcolor = "#0d151f";
        }
    }
});
