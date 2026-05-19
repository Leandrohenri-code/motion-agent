#!/usr/bin/env python3
"""
Motion Agent V2 — Orquestrador principal.
Arquitetura AI-native cinematic OS com Scene DSL + Runtime Remotion.

Pipeline:
  1. Visual DNA Extraction (imagem de referência → identidade visual)
  2. Creative Direction (brief → conceito cinematográfico)
  3. Per-scene: Scene Planning → DSL Generation → Compile → Write
  4. Coherence Check & Repair (corrige DSLs automaticamente)
  5. Root.tsx update + Remotion render
"""

import sys
import os
import json
import time
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))

from ai_client import AIClient
from visual_dna import VisualDNAExtractor, VisualDNA
from temporal_memory import TemporalMemory
from composition_extractor import CompositionExtractor, CompositionConstraints
from cv_extractor import CVExtractor
from scene_graph import SceneGraph
from motion_planner import MotionPlanner
from motion_dsl import MotionDSL
from delta_patcher import DeltaPatcher
from fidelity_scorer import score as fidelity_score, THRESHOLD_WARN
from agents.creative_director import CreativeDirector
from agents.scene_planner import ScenePlanner
from agents.dsl_generator import DSLGenerator
from agents.coherence_agent import CoherenceAgent
from remotion_compiler import RemotionCompiler
from remotion_writer import RemotionWriter
from remotion_controller import RemotionController
from utils.json_streamer import log, progress, scene_done, awaiting_approval, done, error, send
from utils.image_utils import image_to_base64


def read_stdin_json() -> dict:
    line = sys.stdin.readline()
    return json.loads(line.strip())


def wait_for_approval(scene_num: int) -> dict:
    while True:
        line = sys.stdin.readline()
        if not line:
            time.sleep(0.1)
            continue
        try:
            msg = json.loads(line.strip())
            if msg.get("type") in ("approve_scene", "reject_scene", "abort", "retry_scene"):
                return msg
        except Exception:
            continue


# Provedores com URL fixa — não deixar base_url customizada sobrescrever
_CLOUD_PROVIDERS = {
    "openai", "anthropic", "google", "groq", "mistral", "deepseek",
    "xai", "openrouter", "together", "perplexity", "fireworks",
    "anyscale", "huggingface", "cohere",
}


def build_ai_client(api_cfg: dict, system: str = "") -> AIClient:
    provider = api_cfg.get("provider", "openai")
    # Para provedores cloud, nunca usa base_url customizada (pode ser de sessão anterior)
    if provider in _CLOUD_PROVIDERS:
        base_url = None
    else:
        base_url = api_cfg.get("base_url") or None

    return AIClient(
        provider_id=provider,
        api_key=api_cfg.get("api_key", ""),
        base_url=base_url,
        model=api_cfg.get("model", ""),
        temperature=float(api_cfg.get("temperature", 0.7)),
        max_tokens=int(api_cfg.get("max_tokens", 4096)),
        timeout=int(api_cfg.get("timeout", 120)),
        streaming=False,   # V2 usa complete() para DSL generation
        system_prompt=system,
    )


def run(config: dict):
    project    = config.get("project", {})
    frames     = config.get("frames", [])
    script     = config.get("script", {})
    api_cfg    = config.get("api", {})
    reference  = config.get("reference", {})

    remotion_path      = project.get("remotion_path", "")
    output_path        = project.get("output_path", "") or os.path.join(remotion_path, "output")
    fps                = int(project.get("fps", 30))
    resolution         = project.get("resolution", "1080p")
    step_by_step       = bool(project.get("step_by_step", False))
    coherence_on       = bool(project.get("coherence_check", True))
    locked_ref_mode    = bool(project.get("locked_reference_mode", False))

    style_prompt = script.get("execution_prompt", "")
    style_chips  = script.get("style", {})

    # Enriquece o prompt com chips de estilo
    chip_parts = []
    if style_chips.get("rhythm"):      chip_parts.append(f"Rhythm: {style_chips['rhythm']}")
    if style_chips.get("tone"):        chip_parts.append(f"Tone: {style_chips['tone']}")
    if style_chips.get("transitions"): chip_parts.append(f"Transitions: {style_chips['transitions']}")
    if style_chips.get("typography"):  chip_parts.append(f"Typography: {style_chips['typography']}")
    if chip_parts:
        style_prompt += "\n\nStyle chips: " + " | ".join(chip_parts)

    if not frames:
        error("Nenhuma cena configurada.", retryable=False)
        return

    if not remotion_path or not os.path.isdir(remotion_path):
        error(f"Caminho do projeto Remotion inválido: '{remotion_path}'", retryable=False)
        return

    # ── Clientes de IA ─────────────────────────────────────────────────────
    log(f"Inicializando Motion Agent V2 — provider: {api_cfg.get('provider')} | modelo: {api_cfg.get('model')}")

    main_client = build_ai_client(api_cfg)

    vision_model = api_cfg.get("vision_model") or api_cfg.get("model")
    vision_cfg = {**api_cfg, "model": vision_model, "streaming": False}
    vision_client = build_ai_client(vision_cfg)

    # ── Agentes V2 ─────────────────────────────────────────────────────────
    dna_extractor         = VisualDNAExtractor(vision_client)
    composition_extractor = CompositionExtractor(vision_client)
    cv_extractor          = CVExtractor(vision_client)          # SceneGraph determinístico
    creative_director     = CreativeDirector(main_client)
    scene_planner         = ScenePlanner(main_client)
    dsl_generator         = DSLGenerator(vision_client)
    motion_planner        = MotionPlanner(main_client)          # LLM como motion operator
    delta_patcher         = DeltaPatcher(motion_planner)        # patch-based feedback
    coherence_agent       = CoherenceAgent(main_client)
    compiler              = RemotionCompiler()
    writer                = RemotionWriter(remotion_path)
    memory                = TemporalMemory()

    # ── Infraestrutura ─────────────────────────────────────────────────────
    controller = RemotionController(remotion_path, output_path)
    if not controller.is_remotion_installed():
        log("Instalando dependências do projeto Remotion...")
        try:
            controller.install_dependencies()
        except Exception as e:
            error(f"Falha ao instalar dependências: {e}", retryable=False)
            return

    # Garante que o MotionRuntime.tsx existe no projeto
    try:
        runtime_path = writer.ensure_runtime()
        log(f"MotionRuntime.tsx pronto: {os.path.basename(os.path.dirname(runtime_path))}/runtime/")
    except Exception as e:
        log(f"Aviso: runtime não instalado — {e}", level="warn")

    # Garante que o CinematicRuntime.tsx existe no projeto
    runtime_dir = os.path.join(remotion_path, "src", "runtime")
    try:
        cinematic_path = compiler.ensure_cinematic_runtime(runtime_dir)
        log(f"CinematicRuntime.tsx pronto: {os.path.basename(os.path.dirname(cinematic_path))}/runtime/")
    except Exception as e:
        log(f"Aviso: CinematicRuntime não instalado — {e}", level="warn")

    total = len(frames)

    # ── FASE 1: Visual DNA Extraction ───────────────────────────────────────
    log("FASE 1 — Extraindo Visual DNA...")
    dna = _extract_dna(dna_extractor, reference, style_prompt, frames)
    memory.dna = dna
    log(f"DNA extraído: mood={dna.cinematic_mood} | motion={dna.motion_signature} | palette={len(dna.palette)} cores")

    # ── FASE 1b: Composition Extraction (modo referência bloqueada) ──────────
    # Mapa de composition_constraints por índice de frame (só frames com imagem)
    frame_constraints: dict[int, CompositionConstraints] = {}
    if locked_ref_mode:
        log("FASE 1b — Extraindo composição dos frames (Locked Reference Mode)...")
        for i, frame in enumerate(frames):
            img = frame.get("preview") or None
            if img:
                try:
                    constraints = composition_extractor.extract(img)
                    frame_constraints[i] = constraints
                    el_count = len(constraints.locked_elements)
                    log(f"  Frame {i+1}: {el_count} elementos bloqueados | composição={constraints.composition_style}")
                except Exception as e:
                    log(f"  Frame {i+1}: extração de composição falhou ({e}) — usando fallback", level="warn")
                    frame_constraints[i] = composition_extractor.extract_fallback()
        if frame_constraints:
            log(f"Composição extraída: {len(frame_constraints)}/{len(frames)} frames mapeados")
        else:
            log("Nenhuma imagem para extração de composição — modo criativo ativo", level="warn")

    # ── FASE 2: Creative Direction ──────────────────────────────────────────
    log("FASE 2 — Direção criativa...")
    try:
        creative_brief = creative_director.interpret_brief(frames, style_prompt, dna)
        concept = creative_brief.get("concept", "")
        log(f"Conceito: {concept[:80]}")
    except Exception as e:
        log(f"Creative Director falhou (usando fallback): {e}", level="warn")
        creative_brief = {"concept": style_prompt[:60], "narrative_arc": [], "pacing_notes": ""}

    # ── FASE 3: Geração de Cenas ────────────────────────────────────────────
    log("FASE 3 — Gerando cenas via DSL...")
    generated_dsls = []
    generated_codes = []

    for i, frame in enumerate(frames):
        scene_num = i + 1
        description = frame.get("description", "").strip()
        frame_image = frame.get("preview") or None   # base64 da imagem de referência

        progress(scene_num, total, "gerando", percent=int((i / total) * 100))
        log(f"Cena {scene_num}/{total}: {description[:60] or '(sem descrição)'}", scene=scene_num)

        # Se não tem descrição mas tem imagem, gera descrição via visão
        if not description and frame_image:
            log(f"Descrevendo imagem da cena {scene_num}...", scene=scene_num)
            description = _describe_image(vision_client, frame)
            frame = {**frame, "description": description}
            if description:
                log(f"Descrição: {description[:80]}", scene=scene_num)

        # Constraints de composição para este frame
        constraints = frame_constraints.get(i) if locked_ref_mode else None
        is_locked = locked_ref_mode and (frame_image is not None)

        # Modo determinístico: ativado quando há imagem (locked ou não)
        use_cinematic = frame_image is not None

        if is_locked:
            log(f"  🔒 Locked Reference Mode — composição preservada", scene=scene_num)

        # Direção criativa para esta cena
        creative_dir = creative_director.get_scene_direction(scene_num, frame, creative_brief, dna)

        # Câmera sugerida
        prev_cameras = [m.camera_motion for m in memory.mid_term]
        camera_motion = creative_director.suggest_camera_for_scene(scene_num, total, prev_cameras, dna)

        # Guarda SceneGraph e MotionDSL para delta patching no loop de aprovação
        scene_graph: Optional[SceneGraph] = None
        motion_dsl_obj: Optional[MotionDSL] = None

        # ── Função interna: pipeline determinístico ──────────────────────────
        def _generate_cinematic(current_frame, current_image, regen_motion=None):
            """
            Pipeline determinístico: imagem → SceneGraph → MotionDSL → TSX.
            regen_motion: MotionDSL já patcheado para re-compilar sem LLM.
            Retorna (scene_graph, motion_dsl, code).
            """
            nonlocal scene_graph, motion_dsl_obj

            # ── Extrai SceneGraph (só na 1ª geração ou se não tiver) ─────────
            sg = scene_graph
            if sg is None:
                try:
                    log(f"  🔍 Extraindo SceneGraph da cena {scene_num}...", scene=scene_num)
                    sg = cv_extractor.extract(current_image)
                    scene_graph = sg
                    log(f"  SceneGraph: {len(sg.layers)} layers | composição={sg.composition_style}",
                        scene=scene_num)
                except Exception as e:
                    log(f"  CVExtractor falhou ({e}) — usando SceneGraph mínimo", level="warn", scene=scene_num)
                    sg = cv_extractor._fallback_scene_graph(current_image)
                    scene_graph = sg

            # ── Planeja MotionDSL (ou usa versão patcheada) ──────────────────
            if regen_motion is not None:
                md = regen_motion
            else:
                try:
                    log(f"  🎬 Planejando movimento da cena {scene_num}...", scene=scene_num)
                    md = motion_planner.plan(
                        scene_num=scene_num,
                        total_scenes=total,
                        frame=current_frame,
                        scene_graph=sg,
                        dna=dna,
                        memory=memory,
                        creative_brief=creative_brief,
                        fps=fps,
                    )
                except Exception as e:
                    log(f"  MotionPlanner falhou ({e}) — usando fallback", level="warn", scene=scene_num)
                    md = motion_planner._fallback_motion(
                        scene_num,
                        int(float(current_frame.get("duration", 3)) * fps),
                        fps, dna,
                        scene_num == 1, scene_num == total
                    )
            motion_dsl_obj = md

            # ── Fidelity Score ───────────────────────────────────────────────
            try:
                from fidelity_scorer import THRESHOLD_WARN as _WARN
                fidelity = fidelity_score(sg, md)
                for line in fidelity.to_log_lines():
                    level = "warn" if fidelity.score < _WARN else "info"
                    log(line, scene=scene_num, level=level)
                if fidelity.auto_reject:
                    log(f"  ⚠ Fidelidade baixa ({fidelity.score:.0f}/100) — usando fallback motion",
                        level="warn", scene=scene_num)
                    md = motion_planner._fallback_motion(
                        scene_num,
                        int(float(current_frame.get("duration", 3)) * fps),
                        fps, dna,
                        scene_num == 1, scene_num == total
                    )
                    motion_dsl_obj = md
            except Exception:
                pass

            # ── Compila TSX determinístico ───────────────────────────────────
            code = compiler.compile_cinematic(sg, md)
            return sg, md, code

        # ── Função interna: pipeline legado (criativo — sem imagem) ──────────
        def _generate_scene(current_frame, current_description, current_image, regen_feedback=""):
            """Tenta gerar o DSL com retry. Retorna (dsl, code)."""
            _retry = 0
            _max = 2
            _img = current_image
            while _retry <= _max:
                try:
                    log(f"  Planejando cena {scene_num}...", scene=scene_num)
                    plan = scene_planner.plan_scene(
                        scene_num=scene_num,
                        frame=current_frame,
                        dna=dna,
                        camera_motion=camera_motion,
                        fps=fps,
                        creative_direction=creative_dir,
                    )
                    mode_tag = "🔒 locked" if is_locked else ("com imagem" if _img else "texto")
                    log(f"  Gerando DSL da cena {scene_num} [{mode_tag}]" +
                        (f" [feedback: {regen_feedback[:40]}]" if regen_feedback else "") +
                        "...", scene=scene_num)
                    _dsl = dsl_generator.generate(
                        scene_num=scene_num,
                        frame=current_frame,
                        dna=dna,
                        memory=memory,
                        scene_plan=plan,
                        creative_direction=creative_dir,
                        total_scenes=total,
                        fps=fps,
                        frame_image=_img,
                        locked_composition=is_locked,
                        composition_constraints=constraints,
                    )
                    _code = compiler.compile(_dsl)
                    return _dsl, _code
                except Exception as e:
                    _retry += 1
                    err_str = str(e)
                    if _img and any(k in err_str for k in ("400", "429", "image", "vision", "unsupported")):
                        log(f"  Imagem causou erro ({err_str[:60]}), próxima tentativa sem imagem.",
                            level="warn")
                        _img = None
                        if _retry <= _max:
                            time.sleep(3)
                            continue
                    if _retry > _max:
                        log(f"Cena {scene_num} falhou após {_max} tentativas: {e}", level="warn")
                        _dsl = dsl_generator._fallback_dsl(
                            scene_num, current_description,
                            int(float(current_frame.get("duration", 3)) * fps),
                            fps, dna
                        )
                        return _dsl, compiler.compile(_dsl)
                    log(f"  Tentativa {_retry} falhou, retentando...", level="warn")
                    time.sleep(5 * _retry)

        # ── Primeira geração ─────────────────────────────────────────────────
        if use_cinematic:
            log(f"  🎥 Pipeline determinístico (CinematicRuntime)", scene=scene_num)
            try:
                sg, md, code = _generate_cinematic(frame, frame_image)
                dsl = md   # MotionDSL usado como "dsl" no pipeline de coerência
            except Exception as e:
                log(f"  Pipeline cinematic falhou ({e}), fallback para pipeline legado", level="warn",
                    scene=scene_num)
                use_cinematic = False
                dsl, code = _generate_scene(frame, description, frame_image)
        else:
            dsl, code = _generate_scene(frame, description, frame_image)

        # ── Salva + atualiza Root.tsx ────────────────────────────────────────
        def _save_and_refresh(s_num, s_code, s_dsl, s_frame):
            try:
                fp = writer.write_scene(s_num, s_code)
                log(f"Cena {s_num} salva: {os.path.basename(fp)}", scene=s_num)
            except Exception as e:
                error(f"Erro ao salvar cena {s_num}: {e}", scene=s_num)
            try:
                writer.scene_done(s_num, float(s_frame.get("duration", 3)), fps=fps, resolution=resolution)
            except Exception as e:
                log(f"Aviso: Root.tsx não atualizado: {e}", level="warn")

        _save_and_refresh(scene_num, code, dsl, frame)

        generated_dsls.append(dsl)
        generated_codes.append(code)
        scene_done(scene_num, code)
        progress(scene_num, total, "concluída", percent=int(((i + 1) / total) * 100))

        # Atualiza memória temporal
        if dsl:
            dsl_dict = dsl.to_dict() if hasattr(dsl, "to_dict") else {}
            memory.record_scene(scene_num, dsl_dict, frame)
            log(f"  Memória: {len(memory.mid_term)} cenas | DNA: {len(dna.palette)} cores", scene=scene_num)

        # ── Modo passo a passo: loop até aprovação explícita ─────────────────
        if step_by_step:
            regen_count = 0
            while True:
                awaiting_approval(scene_num)
                approval = wait_for_approval(scene_num)
                atype = approval.get("type")

                if atype == "abort":
                    log("Geração abortada pelo usuário.", level="warn")
                    return

                if atype == "approve_scene":
                    log(f"Cena {scene_num} aprovada.", scene=scene_num)
                    break  # ← só sai do loop de aprovação quando aprovada

                # reject_scene ou retry_scene → regenera e volta ao topo do loop
                regen_count += 1
                feedback = approval.get("feedback", "")
                if feedback:
                    log(f"Cena {scene_num} rejeitada (#{regen_count}). Feedback: {feedback}",
                        level="warn", scene=scene_num)
                else:
                    log(f"Cena {scene_num} — regenerando (#{regen_count})...",
                        level="warn", scene=scene_num)

                progress(scene_num, total, "regenerando")
                try:
                    if use_cinematic and motion_dsl_obj is not None and feedback:
                        # ── Delta patch: nunca regenera a cena inteira ───────
                        log(f"  🔧 Aplicando delta patch [{feedback[:50]}]", scene=scene_num)
                        patched_motion = delta_patcher.apply(
                            feedback, motion_dsl_obj, scene_graph, dna
                        )
                        sg, md, code = _generate_cinematic(frame, frame_image, regen_motion=patched_motion)
                        dsl = md
                    elif use_cinematic:
                        # Retry completo no pipeline cinematic (sem feedback ou sem motion_dsl)
                        scene_graph = None   # força re-extração do SceneGraph
                        sg, md, code = _generate_cinematic(frame, frame_image)
                        dsl = md
                    else:
                        # Pipeline legado
                        regen_frame = {**frame, "description": f"{description}\n\nFeedback do revisor: {feedback}"} \
                            if feedback else frame
                        dsl, code = _generate_scene(regen_frame, description, frame_image, feedback)

                    _save_and_refresh(scene_num, code, dsl, frame)
                    generated_dsls[-1] = dsl
                    generated_codes[-1] = code
                    scene_done(scene_num, code)
                    log(f"Cena {scene_num} regenerada — aguardando nova revisão.", scene=scene_num)
                except Exception as e:
                    log(f"Regeneração falhou: {e}", level="warn")

    # ── FASE 4: Coherence Check & Repair ────────────────────────────────────
    if coherence_on and len(generated_dsls) >= 2:
        log("FASE 4 — Verificação e reparo de coerência...")
        try:
            valid_dsls = [d for d in generated_dsls if d is not None]
            report = coherence_agent.check_and_repair(valid_dsls, dna)
            for line in coherence_agent.summarize_for_log(report):
                log(line)

            # Re-compila cenas que foram patcheadas
            if report.patches_applied > 0:
                log(f"Re-compilando {report.patches_applied} cena(s) patcheada(s)...")
                for j, dsl in enumerate(valid_dsls):
                    new_code = compiler.compile(dsl)
                    writer.write_scene(dsl.scene_id, new_code)
                    generated_codes[j] = new_code
        except Exception as e:
            log(f"Coerência ignorada: {e}", level="warn")

    # ── FASE 5: Root.tsx + Render ────────────────────────────────────────────
    log("FASE 5 — Atualizando Root.tsx...")
    try:
        scene_meta = [{"duration": float(f.get("duration", 3))} for f in frames]
        writer.update_root(scene_meta, fps=fps, resolution=resolution)
        log("Root.tsx atualizado.")
    except Exception as e:
        log(f"Erro ao atualizar Root.tsx: {e}", level="warn")

    log("Iniciando renderização via Remotion CLI...")
    try:
        output_file = controller.render(fps=fps)
        done(output_file)
    except Exception as e:
        error(
            f"Renderização falhou: {e}. Os arquivos .tsx foram gerados em {remotion_path}/src/scenes/",
            retryable=True,
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_dna(
    extractor: VisualDNAExtractor,
    reference: dict,
    style_prompt: str,
    frames: list,
) -> VisualDNA:
    """Extrai o Visual DNA da referência ou do prompt."""
    # Tenta imagem de referência
    ref_image = reference.get("preview") or reference.get("image")
    ref_desc = reference.get("manualDescription", "")
    ref_analysis = reference.get("analysis", "")

    if ref_image:
        try:
            return extractor.extract_from_image(ref_image, ref_desc or style_prompt)
        except Exception as e:
            log(f"Extração de DNA por imagem falhou: {e}", level="warn")

    # Tenta análise de referência gerada anteriormente
    if ref_analysis:
        try:
            return extractor.extract_from_description(ref_analysis)
        except Exception:
            pass

    # Tenta pelo prompt de estilo
    if style_prompt:
        try:
            return extractor.extract_from_description(style_prompt)
        except Exception:
            pass

    # Fallback
    return extractor._fallback_dna(style_prompt)


def _describe_image(client: AIClient, frame: dict) -> str:
    """Gera descrição de uma imagem para a cena. Degrada para texto se o modelo não suportar visão."""
    img = frame.get("preview", "")
    if not img:
        return ""
    prompt = (
        "Descreva esta imagem de forma precisa para uso em motion design: "
        "elementos visuais presentes, cores, composição, mood. "
        "Máximo 2 frases, foco em elementos que podem ser animados."
    )
    try:
        return client.complete(prompt, images=[img])
    except Exception as e:
        # Modelo sem suporte a visão — tenta extrair contexto do nome/path da imagem
        msg = str(e).lower()
        if any(k in msg for k in ("400", "image", "vision", "unsupported", "multimodal")):
            return ""   # sem descrição, o DNA e o plano de cena compensam
        return ""


if __name__ == "__main__":
    try:
        config = read_stdin_json()
        run(config)
    except KeyboardInterrupt:
        log("Interrompido.", level="warn")
    except Exception as e:
        import traceback
        error(f"Erro fatal: {e}\n{traceback.format_exc()}", retryable=False)
        sys.exit(1)
