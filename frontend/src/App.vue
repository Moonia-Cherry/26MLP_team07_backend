<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import {
  api,
  type DatasetSpec,
  type ExperimentResult,
  type HealthResponse,
  type ModelSpec,
  type Variant,
} from "./api";

const health = ref<HealthResponse | null>(null);
const models = ref<ModelSpec[]>([]);
const datasets = ref<DatasetSpec[]>([]);
const result = ref<ExperimentResult | null>(null);
const loading = ref(true);
const submitting = ref(false);
const error = ref("");
const paramsText = ref("{}");

const form = reactive({
  model: "",
  variant: "base" as Variant,
  dataset: "",
  test_size: 0.2,
  random_state: 42,
});

const backendAvailable = computed(() => health.value?.ml_backend.available === true);
const selectedModel = computed(() => models.value.find((item) => item.id === form.model));
const compatibleDatasets = computed(() => {
  if (!selectedModel.value) return datasets.value;
  return datasets.value.filter(
    (dataset) => dataset.task_type === selectedModel.value?.task_type,
  );
});

async function loadStatus() {
  loading.value = true;
  error.value = "";
  result.value = null;
  try {
    health.value = await api.health();
    if (!health.value.ml_backend.available) return;
    [models.value, datasets.value] = await Promise.all([api.models(), api.datasets()]);
    form.model = models.value[0]?.id ?? "";
    form.variant = models.value[0]?.variants[0] ?? "base";
    form.dataset = compatibleDatasets.value[0]?.id ?? "";
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : "无法连接后端";
  } finally {
    loading.value = false;
  }
}

function syncSelection() {
  const model = selectedModel.value;
  if (model && !model.variants.includes(form.variant)) {
    form.variant = model.variants[0] ?? "base";
  }
  if (!compatibleDatasets.value.some((dataset) => dataset.id === form.dataset)) {
    form.dataset = compatibleDatasets.value[0]?.id ?? "";
  }
}

async function submitExperiment() {
  error.value = "";
  result.value = null;
  let params: Record<string, unknown>;
  try {
    const parsed = JSON.parse(paramsText.value) as unknown;
    if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
      throw new Error("参数必须是 JSON 对象");
    }
    params = parsed as Record<string, unknown>;
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : "参数 JSON 无效";
    return;
  }

  submitting.value = true;
  try {
    result.value = await api.runExperiment({ ...form, params });
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : "实验执行失败";
  } finally {
    submitting.value = false;
  }
}

onMounted(loadStatus);
</script>

<template>
  <main class="shell">
    <header class="hero">
      <p class="eyebrow">MACHINE LEARNING THEORY &amp; PRACTICE</p>
      <h1>机器学习实验交互平台</h1>
      <p class="lede">Vue 负责交互，FastAPI 负责 HTTP，算法能力来自独立的 ml_core 公共包。</p>
    </header>

    <section class="panel status-panel" aria-live="polite">
      <div>
        <p class="section-label">服务状态</p>
        <h2>{{ loading ? "正在检查连接…" : "Interaction API 已启动" }}</h2>
      </div>
      <span
        class="status-pill"
        :class="backendAvailable ? 'status-ready' : 'status-waiting'"
      >
        {{ backendAvailable ? "ML 已连接" : "ML 待接入" }}
      </span>
      <p v-if="health" class="status-detail">{{ health.ml_backend.detail }}</p>
      <button class="secondary-button" type="button" :disabled="loading" @click="loadStatus">
        重新检查
      </button>
    </section>

    <section v-if="!loading && !backendAvailable" class="notice">
      <strong>真实实验尚未开放。</strong>
      当前仓库没有伪造模型或实验结果；待独立 ML 仓库提供约定的
      <code>ml_core</code> 公共 API 后，此页面会自动启用实验表单。
    </section>

    <section v-if="backendAvailable" class="panel">
      <div class="section-heading">
        <div>
          <p class="section-label">实验配置</p>
          <h2>运行真实 ML 实验</h2>
        </div>
        <p>模型、数据集、训练和评估均由 ml_core 负责。</p>
      </div>

      <form class="experiment-form" @submit.prevent="submitExperiment">
        <label>
          模型
          <select v-model="form.model" required @change="syncSelection">
            <option v-for="model in models" :key="model.id" :value="model.id">
              {{ model.name }}
            </option>
          </select>
        </label>
        <label>
          版本
          <select v-model="form.variant" required>
            <option
              v-for="variant in selectedModel?.variants ?? []"
              :key="variant"
              :value="variant"
            >
              {{ variant }}
            </option>
          </select>
        </label>
        <label>
          数据集
          <select v-model="form.dataset" required>
            <option
              v-for="dataset in compatibleDatasets"
              :key="dataset.id"
              :value="dataset.id"
            >
              {{ dataset.name }}
            </option>
          </select>
        </label>
        <label>
          测试集比例
          <input v-model.number="form.test_size" type="number" min="0.01" max="0.99" step="0.01" />
        </label>
        <label>
          随机种子
          <input v-model.number="form.random_state" type="number" />
        </label>
        <label class="wide-field">
          模型参数（JSON）
          <textarea v-model="paramsText" rows="5" spellcheck="false" />
        </label>
        <button class="primary-button" type="submit" :disabled="submitting">
          {{ submitting ? "运行中…" : "运行实验" }}
        </button>
      </form>
    </section>

    <p v-if="error" class="error-message" role="alert">{{ error }}</p>

    <section v-if="result" class="panel result-panel">
      <p class="section-label">实验结果</p>
      <h2>{{ result.model }} / {{ result.variant }}</h2>
      <dl class="metrics-grid">
        <template v-for="(value, key) in result.metrics" :key="key">
          <div>
            <dt>{{ key }}</dt>
            <dd>{{ value }}</dd>
          </div>
        </template>
      </dl>
      <details v-if="Object.keys(result.diagnostics).length">
        <summary>结构化 diagnostics</summary>
        <pre>{{ JSON.stringify(result.diagnostics, null, 2) }}</pre>
      </details>
    </section>
  </main>
</template>
