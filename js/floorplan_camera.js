import { app } from "../../scripts/app.js";

/*
 * FloorPlan Camera Node — Interactive 2D Canvas
 * 
 * Features:
 * - Floor plan image rendered as background
 * - Draggable camera icon (green)
 * - Rotatable direction cone with handle (yellow)
 * - Click anywhere in canvas to place camera
 * - Hidden widgets for cam_x, cam_y, cam_rotation (synced to Python)
 * 
 * Compatible with ComfyUI's LiteGraph fork.
 */

const CANVAS_HEIGHT = 380;
const CAMERA_RADIUS = 12;
const FOV_ANGLE_DEG = 70;
const FOV_LENGTH = 65;
const HANDLE_RADIUS = 7;
const COLORS = {
    bg: "#111114",
    border: "#333",
    camera: "#4ade80",
    cameraDark: "#166534",
    fovFill: "rgba(74, 222, 128, 0.18)",
    fovStroke: "rgba(74, 222, 128, 0.6)",
    handle: "#facc15",
    handleStroke: "#fef9c3",
    label: "#4ade80",
    labelBg: "rgba(0,0,0,0.75)",
    placeholder: "#555",
    grid: "rgba(255,255,255,0.04)",
};

app.registerExtension({
    name: "FloorPlan.CameraNode",

    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        if (nodeData.name !== "FloorPlanCameraNode") return;

        // ── onNodeCreated: init state + hide widgets ──
        const origCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            origCreated?.apply(this, arguments);

            // Internal state
            this._fp_cam_x = 0.5;
            this._fp_cam_y = 0.5;
            this._fp_cam_rot = 0.0;
            this._fp_img = null;       // Image object
            this._fp_dragging = false;
            this._fp_rotating = false;
            this._fp_canvas_rect = null;
            this._fp_rot_handle = null;
            this._fp_last_info = "";

            // Set node size
            this.size = [480, CANVAS_HEIGHT + 260];

            // Hide coordinate widgets from panel
            this._fp_hideWidgets();
        };

        // ── Hide cam_x, cam_y, cam_rotation widgets ──
        nodeType.prototype._fp_hideWidgets = function () {
            const hidden = ["cam_x", "cam_y", "cam_rotation"];
            for (const w of this.widgets || []) {
                if (hidden.includes(w.name)) {
                    w.computeSize = () => [0, -4];
                    w.type = "converted-widget";
                }
            }
        };

        // ── Sync JS state → Python widget values ──
        nodeType.prototype._fp_syncWidgets = function () {
            for (const w of this.widgets || []) {
                if (w.name === "cam_x") w.value = this._fp_cam_x;
                if (w.name === "cam_y") w.value = this._fp_cam_y;
                if (w.name === "cam_rotation") w.value = this._fp_cam_rot;
            }
        };

        // ── Restore state from saved workflow ──
        const origConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            origConfigure?.apply(this, arguments);
            this._fp_hideWidgets();
            for (const w of this.widgets || []) {
                if (w.name === "cam_x") this._fp_cam_x = w.value ?? 0.5;
                if (w.name === "cam_y") this._fp_cam_y = w.value ?? 0.5;
                if (w.name === "cam_rotation") this._fp_cam_rot = w.value ?? 0;
            }
        };

        // ── Load image from execution result ──
        const origExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            origExecuted?.apply(this, arguments);

            if (message?.images?.[0]) {
                const img = message.images[0];
                const url = `/view?filename=${encodeURIComponent(img.filename)}&type=${img.type}&subfolder=${encodeURIComponent(img.subfolder || "")}`;
                const newImg = new Image();
                newImg.crossOrigin = "anonymous";
                newImg.onload = () => {
                    this._fp_img = newImg;
                    this.setDirtyCanvas(true, true);
                };
                newImg.src = url;
            }

            // Capture camera_info from result
            if (message?.camera_info) {
                this._fp_last_info = message.camera_info;
            }
        };

        // ── Try loading image from upstream LoadImage node ──
        const origConnChange = nodeType.prototype.onConnectionsChange;
        nodeType.prototype.onConnectionsChange = function (side, slot, connected, link_info) {
            origConnChange?.apply(this, arguments);
            // side 1 = input, slot 0 = image_plan
            if (side === 1 && slot === 0 && connected && link_info) {
                try {
                    const originNode = app.graph.getNodeById(link_info.origin_id);
                    if (originNode?.imgs?.[0]?.src) {
                        const newImg = new Image();
                        newImg.crossOrigin = "anonymous";
                        newImg.onload = () => {
                            this._fp_img = newImg;
                            this.setDirtyCanvas(true, true);
                        };
                        newImg.src = originNode.imgs[0].src;
                    }
                } catch (e) {
                    // Silently fail — image will load via onExecuted
                }
            }
        };

        // ── Drawing ──
        const origDraw = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function (ctx) {
            origDraw?.apply(this, arguments);
            if (this.flags?.collapsed) return;

            const pad = 10;
            const cy = 8;  // top offset
            const cw = this.size[0] - pad * 2;
            const ch = CANVAS_HEIGHT;

            this._fp_canvas_rect = { x: pad, y: cy, w: cw, h: ch };

            // ── Background ──
            ctx.fillStyle = COLORS.bg;
            ctx.fillRect(pad, cy, cw, ch);

            // ── Grid overlay ──
            ctx.strokeStyle = COLORS.grid;
            ctx.lineWidth = 0.5;
            const gridSize = 30;
            for (let gx = pad + gridSize; gx < pad + cw; gx += gridSize) {
                ctx.beginPath(); ctx.moveTo(gx, cy); ctx.lineTo(gx, cy + ch); ctx.stroke();
            }
            for (let gy = cy + gridSize; gy < cy + ch; gy += gridSize) {
                ctx.beginPath(); ctx.moveTo(pad, gy); ctx.lineTo(pad + cw, gy); ctx.stroke();
            }

            // ── Floor plan image ──
            if (this._fp_img?.complete && this._fp_img.naturalWidth > 0) {
                // Fit image maintaining aspect ratio
                const imgAspect = this._fp_img.naturalWidth / this._fp_img.naturalHeight;
                const canvasAspect = cw / ch;
                let drawW, drawH, drawX, drawY;

                if (imgAspect > canvasAspect) {
                    drawW = cw;
                    drawH = cw / imgAspect;
                    drawX = pad;
                    drawY = cy + (ch - drawH) / 2;
                } else {
                    drawH = ch;
                    drawW = ch * imgAspect;
                    drawX = pad + (cw - drawW) / 2;
                    drawY = cy;
                }

                ctx.globalAlpha = 0.92;
                ctx.drawImage(this._fp_img, drawX, drawY, drawW, drawH);
                ctx.globalAlpha = 1.0;

                // Store actual image draw rect for accurate coordinate mapping
                this._fp_img_rect = { x: drawX, y: drawY, w: drawW, h: drawH };
            } else {
                this._fp_img_rect = null;
                // Placeholder
                ctx.fillStyle = COLORS.placeholder;
                ctx.font = "13px monospace";
                ctx.textAlign = "center";
                ctx.fillText("Connect image_plan to see floor plan", pad + cw / 2, cy + ch / 2 - 8);
                ctx.fillText("▶ drag camera · ◯ rotate handle", pad + cw / 2, cy + ch / 2 + 12);
                ctx.textAlign = "left";
            }

            // ── Border ──
            ctx.strokeStyle = COLORS.border;
            ctx.lineWidth = 1;
            ctx.strokeRect(pad, cy, cw, ch);

            // ── Camera position (absolute in canvas) ──
            const camAbsX = pad + this._fp_cam_x * cw;
            const camAbsY = cy + this._fp_cam_y * ch;

            // Rotation in radians (0° = up/north, clockwise)
            const rotRad = (this._fp_cam_rot - 90) * Math.PI / 180;
            const halfFov = (FOV_ANGLE_DEG / 2) * Math.PI / 180;

            // ── FOV cone ──
            ctx.beginPath();
            ctx.moveTo(camAbsX, camAbsY);
            ctx.lineTo(
                camAbsX + Math.cos(rotRad - halfFov) * FOV_LENGTH,
                camAbsY + Math.sin(rotRad - halfFov) * FOV_LENGTH
            );
            ctx.arc(camAbsX, camAbsY, FOV_LENGTH, rotRad - halfFov, rotRad + halfFov);
            ctx.closePath();
            ctx.fillStyle = COLORS.fovFill;
            ctx.fill();
            ctx.strokeStyle = COLORS.fovStroke;
            ctx.lineWidth = 1;
            ctx.stroke();

            // ── Direction line ──
            ctx.beginPath();
            ctx.moveTo(camAbsX, camAbsY);
            ctx.lineTo(
                camAbsX + Math.cos(rotRad) * (FOV_LENGTH + 5),
                camAbsY + Math.sin(rotRad) * (FOV_LENGTH + 5)
            );
            ctx.strokeStyle = COLORS.camera;
            ctx.lineWidth = 1.5;
            ctx.setLineDash([4, 3]);
            ctx.stroke();
            ctx.setLineDash([]);

            // ── Camera icon (circle + lens indicator) ──
            ctx.save();
            ctx.translate(camAbsX, camAbsY);

            // Outer ring
            ctx.beginPath();
            ctx.arc(0, 0, CAMERA_RADIUS, 0, Math.PI * 2);
            ctx.fillStyle = COLORS.cameraDark;
            ctx.fill();
            ctx.strokeStyle = COLORS.camera;
            ctx.lineWidth = 2;
            ctx.stroke();

            // Inner dot
            ctx.beginPath();
            ctx.arc(0, 0, 3, 0, Math.PI * 2);
            ctx.fillStyle = COLORS.camera;
            ctx.fill();

            // Direction tick
            ctx.rotate(rotRad);
            ctx.beginPath();
            ctx.moveTo(CAMERA_RADIUS - 3, 0);
            ctx.lineTo(CAMERA_RADIUS + 4, 0);
            ctx.strokeStyle = COLORS.camera;
            ctx.lineWidth = 2.5;
            ctx.stroke();

            ctx.restore();

            // ── Rotation handle (yellow circle at tip of cone) ──
            const handleDist = FOV_LENGTH + 15;
            const hx = camAbsX + Math.cos(rotRad) * handleDist;
            const hy = camAbsY + Math.sin(rotRad) * handleDist;

            ctx.beginPath();
            ctx.arc(hx, hy, HANDLE_RADIUS, 0, Math.PI * 2);
            ctx.fillStyle = COLORS.handle;
            ctx.fill();
            ctx.strokeStyle = COLORS.handleStroke;
            ctx.lineWidth = 1.5;
            ctx.stroke();

            // Small rotation icon inside handle
            ctx.beginPath();
            ctx.arc(hx, hy, 3.5, 0, Math.PI * 1.5);
            ctx.strokeStyle = "#78350f";
            ctx.lineWidth = 1.5;
            ctx.stroke();

            this._fp_rot_handle = { x: hx, y: hy };

            // ── Info bar at bottom of canvas ──
            const barH = 22;
            ctx.fillStyle = COLORS.labelBg;
            ctx.fillRect(pad, cy + ch - barH, cw, barH);

            ctx.fillStyle = COLORS.label;
            ctx.font = "11px monospace";
            ctx.textAlign = "left";

            const cardinal = this._fp_getCardinal(this._fp_cam_rot);
            const infoText = `📐 (${(this._fp_cam_x * 100).toFixed(0)}%, ${(this._fp_cam_y * 100).toFixed(0)}%)  🧭 ${this._fp_cam_rot.toFixed(1)}° ${cardinal}`;
            ctx.fillText(infoText, pad + 8, cy + ch - 7);
            ctx.textAlign = "left";
        };

        // ── Helper: cardinal direction ──
        nodeType.prototype._fp_getCardinal = function (deg) {
            const dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
            const idx = Math.round(((deg % 360) + 360) % 360 / 45) % 8;
            return dirs[idx];
        };

        // ── Mouse: Down ──
        const origMouseDown = nodeType.prototype.onMouseDown;
        nodeType.prototype.onMouseDown = function (event, pos, graphCanvas) {
            const r = this._fp_canvas_rect;
            if (!r) return origMouseDown?.apply(this, arguments) ?? false;

            const [mx, my] = pos;

            // Only handle clicks inside canvas area
            if (mx < r.x || mx > r.x + r.w || my < r.y || my > r.y + r.h) {
                return origMouseDown?.apply(this, arguments) ?? false;
            }

            // Hit-test rotation handle first (priority)
            if (this._fp_rot_handle) {
                const dx = mx - this._fp_rot_handle.x;
                const dy = my - this._fp_rot_handle.y;
                if (dx * dx + dy * dy < (HANDLE_RADIUS + 5) * (HANDLE_RADIUS + 5)) {
                    this._fp_rotating = true;
                    return true;
                }
            }

            // Hit-test camera icon
            const camAbsX = r.x + this._fp_cam_x * r.w;
            const camAbsY = r.y + this._fp_cam_y * r.h;
            const dx = mx - camAbsX;
            const dy = my - camAbsY;
            if (dx * dx + dy * dy < (CAMERA_RADIUS + 4) * (CAMERA_RADIUS + 4)) {
                this._fp_dragging = true;
                return true;
            }

            // Click anywhere in canvas → teleport camera there
            this._fp_cam_x = Math.max(0, Math.min(1, (mx - r.x) / r.w));
            this._fp_cam_y = Math.max(0, Math.min(1, (my - r.y) / r.h));
            this._fp_dragging = true;
            this._fp_syncWidgets();
            this.setDirtyCanvas(true, true);
            return true;
        };

        // ── Mouse: Move ──
        const origMouseMove = nodeType.prototype.onMouseMove;
        nodeType.prototype.onMouseMove = function (event, pos, graphCanvas) {
            const r = this._fp_canvas_rect;
            if (!r) return origMouseMove?.apply(this, arguments) ?? false;

            const [mx, my] = pos;

            if (this._fp_dragging) {
                this._fp_cam_x = Math.max(0, Math.min(1, (mx - r.x) / r.w));
                this._fp_cam_y = Math.max(0, Math.min(1, (my - r.y) / r.h));
                this._fp_syncWidgets();
                this.setDirtyCanvas(true, true);
                return true;
            }

            if (this._fp_rotating) {
                const camAbsX = r.x + this._fp_cam_x * r.w;
                const camAbsY = r.y + this._fp_cam_y * r.h;
                const angle = Math.atan2(my - camAbsY, mx - camAbsX);
                this._fp_cam_rot = ((angle * 180 / Math.PI) + 90 + 360) % 360;
                this._fp_syncWidgets();
                this.setDirtyCanvas(true, true);
                return true;
            }

            return origMouseMove?.apply(this, arguments) ?? false;
        };

        // ── Mouse: Up ──
        const origMouseUp = nodeType.prototype.onMouseUp;
        nodeType.prototype.onMouseUp = function (event, pos, graphCanvas) {
            if (this._fp_dragging || this._fp_rotating) {
                this._fp_dragging = false;
                this._fp_rotating = false;
                return true;
            }
            return origMouseUp?.apply(this, arguments) ?? false;
        };
    },

    // ── Also register MaterialRefNode styling ──
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
