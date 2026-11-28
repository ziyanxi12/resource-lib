"""组件 ↔ Pixso 组件映射（ds_component_mapping）

一行 = 一个设计系统的 HTML 组件到 Pixso 组件集的映射。
HTML 侧字段（slug/component_name/html_zh/html_group）由组件包入库自动同步
（POST /{slug}/mapping/sync + import_parts 自动挂钩）；Pixso 侧字段
（pixso_name/pixso_guid/…）由匹配脚本批量回填（阶段 2，格式定稿后启用 PUT /{slug}/mapping）。
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, String, Text, UniqueConstraint

from app.database import Base


class DsComponentMapping(Base):
    __tablename__ = "ds_component_mappings"
    __table_args__ = (
        UniqueConstraint("slug", "component_name", name="uq_ds_mapping_slug_component"),
        Index("idx_ds_mapping_slug", "slug"),
        Index("uq_ds_mapping_uuid", "mapping_uuid", unique=True),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    # ── 行唯一标识（2026-11：原型代码嵌入——代码转设计稿时经 GET /mapping 按 uuid 反查映射行）──
    # UUIDv4 服务端生成：sync 新插行赋值、已有行永不重生成（组件删除重建视为新映射）；
    # 客户端不可写（不在 _UPDATABLE_FIELDS）；存量行启动时回填。
    # 唯一性保证：v4 有 122 位随机量（碰撞概率 ~2^-61/对），另有上方唯一索引硬兜底——
    # 万一碰撞插入报错而非静默重复。
    mapping_uuid = Column(String(36), nullable=True, comment="行唯一标识 UUIDv4（原型代码引用键；服务端生成，客户端不可写）")
    # ── HTML 组件侧（sync 入库；join 键 = component_name，与 spec.json 的 name 一致） ──
    slug = Column(String(100), nullable=False, comment="设计系统 slug（多系统共存）")
    component_name = Column(String(255), nullable=False, comment="HTML 组件名（assets/components 下路径段，如 Button）")
    html_zh = Column(String(255), nullable=True, comment="HTML 组件中文名（index.json 的 shortNames；GTS 等无则回落 spec title）")
    html_group = Column(String(255), nullable=True, comment="HTML 组件分组（index.json 路径第一段，如 操作类；无目录为空）")

    # ── Pixso 组件集侧（匹配脚本回填；阶段 2 前恒 NULL） ──
    pixso_name = Column(String(255), nullable=True, comment="Pixso 组件集名（如 Button；普通组件取首段名，如 Pagination）")
    pixso_guid = Column(String(100), nullable=True, comment="Pixso 组件集 node_id（实例创建主锚点：getNodeByIdAsync → children 按变体匹配 → createInstance）")
    file_key = Column(String(100), nullable=True, comment="Pixso 文件 id（拼跳转 url / 跨文件定位；本地组件为所属文件 key）")
    library_name = Column(String(255), nullable=True, comment="组件库名称（订阅列表库名，per-component 展示来源行用）")
    page_id = Column(String(100), nullable=True, comment="Pixso 页 id")
    page_name = Column(String(255), nullable=True, comment="Pixso 页名")
    pixso_category = Column(String(255), nullable=True, comment="Pixso 侧分类（containing_frame.name，如 操作类）")
    component_content_key = Column(String(100), nullable=True, comment="Pixso 组件 40 位内容 hash（变更检测：设计侧改组件 → hash 变 → 提示映射可能过期；非主键）")
    match_type = Column(String(20), nullable=True, comment="匹配方式：exact（名字精确）/ fuzzy（归一化匹配，建议人工复核）/ manual（人工指定，重跑匹配不覆盖）")
    url = Column(Text, nullable=True, comment="Pixso 跳转链接（https://…/app/design/{file_key}?item-id={pixso_guid}；空则渲染端不显示跳转按钮）")
    thumbnail_url = Column(String(512), nullable=True, comment="Pixso 组件缩略图相对路径（图片服务的 /static/…；渲染端拼 origin+/api 前缀访问，匹配时刻从组件库清单 thumbnail_url 拷贝）")
    instance_spec = Column(Text, nullable=True, comment="实例参数 JSON 字符串：{defaults, bridges:{轴名:{axis, values:{html值→pixso值}}}}——runner 翻译 HTML 轴值后在组件集 children 里匹配变体创建实例")
    instance_code = Column(Text, nullable=True, comment="设计组件生成代码字符串（设计师用 AI 生成，处理组件属性；第一期后端不验证格式，存取原样，规范后续定）")

    # ── 状态与审计 ──
    status = Column(String(20), nullable=False, default="missing", comment="aligned（已对齐）/ partial（部分对齐）/ missing（未关联）")
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
