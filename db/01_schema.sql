--
-- PostgreSQL database dump
--

-- Dumped from database version 17.2 (Debian 17.2-1.pgdg120+1)
-- Dumped by pg_dump version 17.2 (Debian 17.2-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: achievementtype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.achievementtype AS ENUM (
    'SPEED',
    'QUALITY',
    'CONSISTENCY',
    'LEARNING',
    'TEAMWORK',
    'INNOVATION'
);


--
-- Name: badgerarity; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.badgerarity AS ENUM (
    'COMMON',
    'RARE',
    'EPIC',
    'LEGENDARY'
);


--
-- Name: communication_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.communication_status AS ENUM (
    'Pendiente',
    'Revisado',
    'En Proceso',
    'Resuelto',
    'Rechazado'
);


--
-- Name: communication_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.communication_type AS ENUM (
    'Sugerencia',
    'Pedido de Material',
    'Queja/Problema',
    'Consulta',
    'Otro',
    'Mensaje Administrativo',
    'Asignación de Tarea',
    'Comunicado'
);


--
-- Name: vacation_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.vacation_status_enum AS ENUM (
    'Solicitado',
    'Aprobado',
    'Rechazado'
);


--
-- Name: update_ai_config_timestamp(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_ai_config_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


--
-- Name: update_checklist_progress_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_checklist_progress_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: absences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.absences (
    id integer NOT NULL,
    user_id integer NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    absence_type character varying(10) NOT NULL,
    notes text,
    created_at date
);


--
-- Name: absences_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.absences_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: absences_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.absences_id_seq OWNED BY public.absences.id;


--
-- Name: achievements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.achievements (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text NOT NULL,
    type public.achievementtype NOT NULL,
    rarity public.badgerarity DEFAULT 'COMMON'::public.badgerarity,
    icon character varying(50) NOT NULL,
    points integer DEFAULT 0,
    condition_json text,
    active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: achievements_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.achievements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: achievements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.achievements_id_seq OWNED BY public.achievements.id;


--
-- Name: ai_configuration; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_configuration (
    id integer NOT NULL,
    config_key character varying(100) NOT NULL,
    config_value jsonb NOT NULL,
    description text,
    config_type character varying(50) DEFAULT 'general'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by_id integer
);


--
-- Name: TABLE ai_configuration; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.ai_configuration IS 'Configuración global del sistema de IA';


--
-- Name: ai_configuration_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ai_configuration_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ai_configuration_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ai_configuration_id_seq OWNED BY public.ai_configuration.id;


--
-- Name: ai_model_performance; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_model_performance (
    id integer NOT NULL,
    model_name character varying(100) NOT NULL,
    model_version character varying(50),
    accuracy double precision,
    precision_score double precision,
    recall_score double precision,
    f1_score double precision,
    predictions_made integer DEFAULT 0,
    correct_predictions integer DEFAULT 0,
    false_positives integer DEFAULT 0,
    false_negatives integer DEFAULT 0,
    evaluation_period_start timestamp without time zone NOT NULL,
    evaluation_period_end timestamp without time zone NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    notes text,
    improvements_needed text,
    CONSTRAINT ai_model_performance_accuracy_check CHECK (((accuracy >= (0)::double precision) AND (accuracy <= (100)::double precision))),
    CONSTRAINT ai_model_performance_f1_score_check CHECK (((f1_score >= (0)::double precision) AND (f1_score <= (100)::double precision))),
    CONSTRAINT ai_model_performance_precision_score_check CHECK (((precision_score >= (0)::double precision) AND (precision_score <= (100)::double precision))),
    CONSTRAINT ai_model_performance_recall_score_check CHECK (((recall_score >= (0)::double precision) AND (recall_score <= (100)::double precision)))
);


--
-- Name: TABLE ai_model_performance; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.ai_model_performance IS 'Métricas de rendimiento y precisión de los modelos de IA';


--
-- Name: ai_model_performance_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ai_model_performance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ai_model_performance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ai_model_performance_id_seq OWNED BY public.ai_model_performance.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: alert_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alert_user (
    alert_id integer NOT NULL,
    user_id integer NOT NULL
);


--
-- Name: alerts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alerts (
    id integer NOT NULL,
    type character varying(50) NOT NULL,
    message text NOT NULL,
    entity_type character varying(50),
    entity_id integer,
    severity character varying(20) DEFAULT 'info'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    resolved boolean DEFAULT false,
    resolved_at timestamp without time zone,
    resolved_by_id integer
);


--
-- Name: alerts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.alerts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: alerts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.alerts_id_seq OWNED BY public.alerts.id;


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    action character varying(50) NOT NULL,
    entity_type character varying(50),
    entity_id integer,
    user_id integer,
    user_name character varying(255),
    user_role character varying(50),
    "timestamp" timestamp with time zone DEFAULT now(),
    ip_address inet,
    user_agent text,
    old_values jsonb,
    new_values jsonb,
    changes_summary text,
    module character varying(50),
    severity character varying(20) DEFAULT 'LOW'::character varying,
    notes text,
    session_id character varying(255)
);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: backup_alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.backup_alembic_version (
    version_num character varying(32)
);


--
-- Name: cause_codes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cause_codes (
    id integer NOT NULL,
    code character varying(50) NOT NULL,
    description character varying(255) NOT NULL,
    active boolean DEFAULT true
);


--
-- Name: cause_codes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cause_codes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cause_codes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cause_codes_id_seq OWNED BY public.cause_codes.id;


--
-- Name: challenge_participations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.challenge_participations (
    id integer NOT NULL,
    challenge_id integer NOT NULL,
    user_id integer NOT NULL,
    current_progress integer DEFAULT 0,
    completed boolean DEFAULT false,
    completed_at timestamp without time zone,
    joined_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: challenge_participations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.challenge_participations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: challenge_participations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.challenge_participations_id_seq OWNED BY public.challenge_participations.id;


--
-- Name: challenges; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.challenges (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text NOT NULL,
    type public.achievementtype NOT NULL,
    points_reward integer NOT NULL,
    start_date timestamp without time zone NOT NULL,
    end_date timestamp without time zone NOT NULL,
    target_value integer NOT NULL,
    condition_json text,
    active boolean DEFAULT true,
    created_by_id integer
);


--
-- Name: challenges_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.challenges_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: challenges_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.challenges_id_seq OWNED BY public.challenges.id;


--
-- Name: checklist_progress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.checklist_progress (
    id integer NOT NULL,
    work_order_id integer NOT NULL,
    task_list_id integer NOT NULL,
    steps_progress jsonb DEFAULT '[]'::jsonb NOT NULL,
    total_elapsed_time real DEFAULT 0.0,
    progress_percent real DEFAULT 0.0,
    is_completed boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_id integer NOT NULL,
    extra_data jsonb
);


--
-- Name: COLUMN checklist_progress.progress_percent; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.checklist_progress.progress_percent IS 'Porcentaje de progreso (0-100)';


--
-- Name: COLUMN checklist_progress.is_completed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.checklist_progress.is_completed IS 'Indica si el checklist está completamente terminado';


--
-- Name: COLUMN checklist_progress.extra_data; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.checklist_progress.extra_data IS 'Datos adicionales en formato JSON';


--
-- Name: checklist_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.checklist_progress_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: checklist_progress_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.checklist_progress_id_seq OWNED BY public.checklist_progress.id;


--
-- Name: communication_reads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.communication_reads (
    id integer NOT NULL,
    communication_id integer NOT NULL,
    user_id integer NOT NULL,
    read_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: communication_reads_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.communication_reads_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: communication_reads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.communication_reads_id_seq OWNED BY public.communication_reads.id;


--
-- Name: communications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.communications (
    id integer NOT NULL,
    type public.communication_type DEFAULT 'Sugerencia'::public.communication_type NOT NULL,
    subject character varying(200) NOT NULL,
    message text NOT NULL,
    status public.communication_status DEFAULT 'Pendiente'::public.communication_status NOT NULL,
    priority character varying(20) DEFAULT 'Normal'::character varying,
    created_by_id integer NOT NULL,
    assigned_to_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now(),
    reviewed_at timestamp with time zone,
    resolved_at timestamp with time zone,
    admin_notes text,
    admin_response text,
    is_anonymous boolean DEFAULT false,
    department character varying(100),
    machine_id integer,
    direction character varying(20) DEFAULT 'Operario a Admin'::character varying NOT NULL,
    target_role_id integer,
    target_department character varying(100),
    read_at timestamp without time zone,
    parent_communication_id integer,
    requires_response boolean DEFAULT false,
    CONSTRAINT communications_priority_check CHECK (((priority)::text = ANY ((ARRAY['Baja'::character varying, 'Normal'::character varying, 'Alta'::character varying, 'Urgente'::character varying])::text[])))
);


--
-- Name: communications_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.communications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: communications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.communications_id_seq OWNED BY public.communications.id;


--
-- Name: document_attachments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.document_attachments (
    id integer NOT NULL,
    file_name character varying NOT NULL,
    original_file_name character varying NOT NULL,
    file_path character varying NOT NULL,
    file_type character varying NOT NULL,
    file_size integer NOT NULL,
    description text,
    uploaded_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    uploaded_by_id integer,
    entity_type character varying NOT NULL,
    entity_id integer NOT NULL
);


--
-- Name: document_attachments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.document_attachments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: document_attachments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.document_attachments_id_seq OWNED BY public.document_attachments.id;


--
-- Name: documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documents (
    id integer NOT NULL,
    filename character varying NOT NULL,
    original_filename character varying NOT NULL,
    type character varying NOT NULL,
    status character varying NOT NULL,
    file_path character varying NOT NULL,
    content text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    processed_at timestamp without time zone,
    error_message character varying,
    created_by_id integer NOT NULL,
    supplier_name character varying,
    total_amount double precision,
    processed_data jsonb
);


--
-- Name: documents_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.documents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: documents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.documents_id_seq OWNED BY public.documents.id;


--
-- Name: failure_codes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.failure_codes (
    id integer NOT NULL,
    code character varying(50) NOT NULL,
    description character varying(255) NOT NULL,
    active boolean DEFAULT true
);


--
-- Name: failure_codes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.failure_codes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: failure_codes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.failure_codes_id_seq OWNED BY public.failure_codes.id;


--
-- Name: failure_patterns; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.failure_patterns (
    id integer NOT NULL,
    pattern_name character varying(100) NOT NULL,
    description text,
    machines_affected jsonb,
    failure_codes jsonb,
    frequency character varying(50),
    conditions jsonb,
    root_causes jsonb,
    preventive_actions jsonb,
    recommended_frequency character varying(50),
    estimated_impact double precision,
    confidence_score double precision,
    occurrences_analyzed integer,
    last_occurrence timestamp without time zone,
    discovered_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    discovered_by_id integer NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying,
    CONSTRAINT failure_patterns_confidence_score_check CHECK (((confidence_score >= (0)::double precision) AND (confidence_score <= (100)::double precision))),
    CONSTRAINT failure_patterns_frequency_check CHECK (((frequency)::text = ANY ((ARRAY['daily'::character varying, 'weekly'::character varying, 'monthly'::character varying, 'seasonal'::character varying, 'random'::character varying])::text[]))),
    CONSTRAINT failure_patterns_status_check CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'validated'::character varying, 'obsolete'::character varying])::text[])))
);


--
-- Name: TABLE failure_patterns; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.failure_patterns IS 'Patrones de fallo identificados automáticamente por IA';


--
-- Name: failure_patterns_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.failure_patterns_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: failure_patterns_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.failure_patterns_id_seq OWNED BY public.failure_patterns.id;


--
-- Name: formats; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.formats (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description character varying(255),
    estimated_setup_time double precision,
    machines_requiring_adjustment json,
    tools_materials_needed json,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    active boolean DEFAULT true,
    updated_at timestamp without time zone
);


--
-- Name: TABLE formats; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.formats IS 'Catálogo de formatos maestros para cambios de formato';


--
-- Name: COLUMN formats.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formats.name IS 'Nombre único del formato';


--
-- Name: COLUMN formats.estimated_setup_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formats.estimated_setup_time IS 'Tiempo estimado de setup en horas';


--
-- Name: COLUMN formats.machines_requiring_adjustment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formats.machines_requiring_adjustment IS 'JSON con IDs de máquinas que requieren ajuste';


--
-- Name: COLUMN formats.tools_materials_needed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formats.tools_materials_needed IS 'JSON con lista de herramientas/materiales necesarios';


--
-- Name: formats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.formats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: formats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.formats_id_seq OWNED BY public.formats.id;


--
-- Name: inventory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inventory (
    id integer NOT NULL,
    product_name character varying(255) NOT NULL,
    quantity integer DEFAULT 0 NOT NULL,
    price numeric(10,2) NOT NULL,
    supplier_id integer,
    warehouse_id integer NOT NULL,
    discount double precision,
    stock_minimo integer DEFAULT 0 NOT NULL,
    tipo character varying(20) DEFAULT 'mecánico'::character varying,
    CONSTRAINT check_tipo_valido CHECK (((tipo)::text = ANY ((ARRAY['mecánico'::character varying, 'eléctrico'::character varying, 'neumático'::character varying, 'limpieza'::character varying])::text[])))
);


--
-- Name: inventory_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.inventory_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: inventory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inventory_id_seq OWNED BY public.inventory.id;


--
-- Name: lines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lines (
    id integer NOT NULL,
    nombre character varying(255) NOT NULL,
    section_id integer NOT NULL
);


--
-- Name: lines_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lines_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lines_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lines_id_seq OWNED BY public.lines.id;


--
-- Name: machine_parts_association; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.machine_parts_association (
    machine_id integer NOT NULL,
    inventory_id integer NOT NULL,
    quantity integer NOT NULL
);


--
-- Name: machine_predictions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.machine_predictions (
    id integer NOT NULL,
    machine_id integer NOT NULL,
    prediction_type character varying(50) DEFAULT 'failure'::character varying NOT NULL,
    probability double precision,
    confidence double precision,
    predicted_date timestamp without time zone,
    prediction_data jsonb,
    components_at_risk jsonb,
    model_used character varying(100),
    data_points_used integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_id integer NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying,
    actual_outcome character varying(50),
    outcome_date timestamp without time zone,
    recommended_actions jsonb,
    CONSTRAINT machine_predictions_actual_outcome_check CHECK (((actual_outcome)::text = ANY ((ARRAY['correct'::character varying, 'false_positive'::character varying, 'false_negative'::character varying])::text[]))),
    CONSTRAINT machine_predictions_confidence_check CHECK (((confidence >= (0)::double precision) AND (confidence <= (100)::double precision))),
    CONSTRAINT machine_predictions_probability_check CHECK (((probability >= (0)::double precision) AND (probability <= (100)::double precision))),
    CONSTRAINT machine_predictions_status_check CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'validated'::character varying, 'expired'::character varying, 'cancelled'::character varying])::text[])))
);


--
-- Name: TABLE machine_predictions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.machine_predictions IS 'Predicciones de mantenimiento generadas por IA para máquinas';


--
-- Name: machine_predictions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.machine_predictions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: machine_predictions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.machine_predictions_id_seq OWNED BY public.machine_predictions.id;


--
-- Name: machines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.machines (
    id integer NOT NULL,
    nombre character varying(255) NOT NULL,
    modelo character varying(255) NOT NULL,
    marca character varying(255) NOT NULL,
    numero_serie character varying(255) NOT NULL,
    section_id integer NOT NULL,
    line_id integer NOT NULL,
    criticidad character varying(50)
);


--
-- Name: machines_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.machines_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: machines_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.machines_id_seq OWNED BY public.machines.id;


--
-- Name: maintenance_backlogs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.maintenance_backlogs (
    id integer NOT NULL,
    title character varying(200) NOT NULL,
    description text,
    priority character varying(20) DEFAULT 'Media'::character varying,
    status character varying(20) DEFAULT 'Pendiente'::character varying,
    machine_id integer,
    section_id integer,
    created_by_id integer NOT NULL,
    assigned_to_id integer,
    estimated_hours integer,
    estimated_downtime integer,
    notes text,
    completion_notes text,
    actual_work_order_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp without time zone
);


--
-- Name: maintenance_backlogs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.maintenance_backlogs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: maintenance_backlogs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.maintenance_backlogs_id_seq OWNED BY public.maintenance_backlogs.id;


--
-- Name: maintenance_optimizations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.maintenance_optimizations (
    id integer NOT NULL,
    section_id integer,
    original_schedule jsonb NOT NULL,
    optimized_schedule jsonb NOT NULL,
    optimization_criteria jsonb,
    estimated_downtime_reduction double precision,
    cost_savings double precision,
    efficiency_improvement double precision,
    generated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    generated_by_id integer NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying,
    CONSTRAINT maintenance_optimizations_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'approved'::character varying, 'implemented'::character varying, 'rejected'::character varying])::text[])))
);


--
-- Name: TABLE maintenance_optimizations; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.maintenance_optimizations IS 'Optimizaciones de cronogramas de mantenimiento propuestas por IA';


--
-- Name: maintenance_optimizations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.maintenance_optimizations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: maintenance_optimizations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.maintenance_optimizations_id_seq OWNED BY public.maintenance_optimizations.id;


--
-- Name: maintenance_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.maintenance_requests (
    id integer NOT NULL,
    title character varying NOT NULL,
    description text,
    reported_by_id integer NOT NULL,
    machine_id integer,
    status character varying DEFAULT 'Pendiente'::character varying NOT NULL,
    priority character varying,
    created_at timestamp without time zone DEFAULT now(),
    reviewed_at timestamp without time zone,
    reviewed_by_id integer,
    review_notes text,
    work_order_id integer
);


--
-- Name: maintenance_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.maintenance_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: maintenance_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.maintenance_requests_id_seq OWNED BY public.maintenance_requests.id;


--
-- Name: maintenances; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.maintenances (
    id integer NOT NULL,
    title character varying(255) NOT NULL,
    type character varying(50) NOT NULL,
    description text NOT NULL,
    machine_id integer NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    assigned_role_id integer,
    assigned_user_id integer,
    frequency character varying(255),
    next_maintenance_date timestamp without time zone,
    last_maintenance_date timestamp without time zone,
    notification_interval integer,
    is_completed boolean DEFAULT false,
    task_list_id integer,
    tipo_regulacion character varying(255),
    organismo_certificador character varying(255),
    numero_certificado character varying(255),
    normativa_aplicable text
);


--
-- Name: maintenances_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.maintenances_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: maintenances_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.maintenances_id_seq OWNED BY public.maintenances.id;


--
-- Name: point_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.point_transactions (
    id integer NOT NULL,
    user_points_id integer NOT NULL,
    points integer NOT NULL,
    reason character varying(200) NOT NULL,
    entity_type character varying(50),
    entity_id integer,
    multiplier real DEFAULT 1.0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: point_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.point_transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: point_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.point_transactions_id_seq OWNED BY public.point_transactions.id;


--
-- Name: remedy_codes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.remedy_codes (
    id integer NOT NULL,
    code character varying(50) NOT NULL,
    description character varying(255) NOT NULL,
    active boolean DEFAULT true
);


--
-- Name: remedy_codes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.remedy_codes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: remedy_codes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.remedy_codes_id_seq OWNED BY public.remedy_codes.id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    id integer NOT NULL,
    nombre character varying(50) NOT NULL
);


--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: sections; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sections (
    id integer NOT NULL,
    nombre character varying(255) NOT NULL
);


--
-- Name: sections_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sections_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sections_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sections_id_seq OWNED BY public.sections.id;


--
-- Name: shift_assignments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shift_assignments (
    id integer NOT NULL,
    user_id integer NOT NULL,
    pattern_id integer NOT NULL,
    offset_days integer NOT NULL,
    reference_date date NOT NULL
);


--
-- Name: shift_assignments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.shift_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: shift_assignments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.shift_assignments_id_seq OWNED BY public.shift_assignments.id;


--
-- Name: shift_overrides; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shift_overrides (
    id integer NOT NULL,
    user_id integer NOT NULL,
    date date NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    actual_shift_code character varying(10) NOT NULL
);


--
-- Name: shift_overrides_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.shift_overrides_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: shift_overrides_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.shift_overrides_id_seq OWNED BY public.shift_overrides.id;


--
-- Name: shift_patterns; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shift_patterns (
    id integer NOT NULL,
    name character varying NOT NULL,
    description text,
    pattern_sequence character varying NOT NULL,
    cycle_length_days integer NOT NULL
);


--
-- Name: shift_patterns_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.shift_patterns_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: shift_patterns_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.shift_patterns_id_seq OWNED BY public.shift_patterns.id;


--
-- Name: supplier_product_prices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.supplier_product_prices (
    id integer NOT NULL,
    product_name character varying(255) NOT NULL,
    supplier_id integer NOT NULL,
    warehouse_id integer,
    price numeric(10,2) NOT NULL,
    discount numeric(5,2) DEFAULT 0.0 NOT NULL,
    last_updated timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: supplier_product_prices_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.supplier_product_prices_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: supplier_product_prices_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.supplier_product_prices_id_seq OWNED BY public.supplier_product_prices.id;


--
-- Name: suppliers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.suppliers (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    company character varying(255) NOT NULL,
    phone character varying(50) NOT NULL
);


--
-- Name: suppliers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.suppliers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: suppliers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.suppliers_id_seq OWNED BY public.suppliers.id;


--
-- Name: task_lists; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.task_lists (
    id integer NOT NULL,
    name character varying NOT NULL,
    description text,
    applies_to_type character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_id integer
);


--
-- Name: task_lists_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.task_lists_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: task_lists_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.task_lists_id_seq OWNED BY public.task_lists.id;


--
-- Name: task_steps; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.task_steps (
    id integer NOT NULL,
    task_list_id integer NOT NULL,
    step_order integer NOT NULL,
    description text NOT NULL,
    estimated_time_minutes integer
);


--
-- Name: task_steps_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.task_steps_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: task_steps_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.task_steps_id_seq OWNED BY public.task_steps.id;


--
-- Name: user_achievements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_achievements (
    id integer NOT NULL,
    user_id integer NOT NULL,
    achievement_id integer NOT NULL,
    earned_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    progress integer DEFAULT 100,
    notified boolean DEFAULT false
);


--
-- Name: user_achievements_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_achievements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_achievements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_achievements_id_seq OWNED BY public.user_achievements.id;


--
-- Name: user_points; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_points (
    id integer NOT NULL,
    user_id integer NOT NULL,
    total_points integer DEFAULT 0,
    weekly_points integer DEFAULT 0,
    monthly_points integer DEFAULT 0,
    current_streak integer DEFAULT 0,
    best_streak integer DEFAULT 0,
    level integer DEFAULT 1,
    experience integer DEFAULT 0,
    last_activity timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: user_points_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_points_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_points_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_points_id_seq OWNED BY public.user_points.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying NOT NULL,
    password character varying NOT NULL,
    role_id integer NOT NULL,
    section_id integer,
    active boolean DEFAULT true NOT NULL,
    email character varying(255),
    hourly_rate double precision DEFAULT 0.0
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: vacation_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vacation_requests (
    id integer NOT NULL,
    user_id integer NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    status public.vacation_status_enum NOT NULL,
    notes text,
    manager_notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    reviewed_by_id integer
);


--
-- Name: vacation_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vacation_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: vacation_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vacation_requests_id_seq OWNED BY public.vacation_requests.id;


--
-- Name: warehouses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.warehouses (
    id integer NOT NULL,
    name character varying(255) NOT NULL
);


--
-- Name: warehouses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.warehouses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: warehouses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.warehouses_id_seq OWNED BY public.warehouses.id;


--
-- Name: work_order_materials; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.work_order_materials (
    id integer NOT NULL,
    work_order_id integer NOT NULL,
    inventory_id integer NOT NULL,
    quantity_used integer DEFAULT 1 NOT NULL,
    unit_cost_at_use numeric(10,2) NOT NULL
);


--
-- Name: work_order_materials_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_order_materials_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: work_order_materials_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.work_order_materials_id_seq OWNED BY public.work_order_materials.id;


--
-- Name: work_order_technicians; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.work_order_technicians (
    id integer NOT NULL,
    work_order_id integer NOT NULL,
    user_id integer NOT NULL,
    role character varying(20) DEFAULT 'apoyo'::character varying NOT NULL,
    assigned_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    assigned_by_id integer,
    hours_worked numeric(5,2) DEFAULT 0.00,
    is_active boolean DEFAULT true,
    notes text,
    CONSTRAINT work_order_technicians_hours_worked_check CHECK ((hours_worked >= (0)::numeric)),
    CONSTRAINT work_order_technicians_role_check CHECK (((role)::text = ANY ((ARRAY['principal'::character varying, 'apoyo'::character varying, 'supervisor'::character varying])::text[])))
);


--
-- Name: work_order_technicians_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_order_technicians_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: work_order_technicians_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.work_order_technicians_id_seq OWNED BY public.work_order_technicians.id;


--
-- Name: work_orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.work_orders (
    id integer NOT NULL,
    order_number character varying(255),
    title text NOT NULL,
    details text,
    work_type character varying(50) NOT NULL,
    section_id integer,
    line_id integer,
    machine_id integer,
    operator character varying NOT NULL,
    assigned_to_id integer NOT NULL,
    status character varying(50) DEFAULT 'Pendiente'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    finished_at timestamp without time zone,
    imagen_url text,
    quantity_used integer DEFAULT 0,
    source_document_id integer,
    failure_code_id integer,
    cause_code_id integer,
    remedy_code_id integer,
    actual_start_time timestamp without time zone,
    actual_end_time timestamp without time zone,
    downtime_hours numeric(10,2),
    completion_notes text,
    format_change_type character varying(50),
    affected_machines json,
    format_from_id integer,
    format_to_id integer,
    format_from_name character varying(100),
    format_to_name character varying(100),
    setup_duration double precision,
    estimated_setup_duration double precision,
    production_loss_hours double precision,
    setup_team json,
    setup_notes text,
    task_list_id integer,
    generated_from_maintenance_id integer,
    total_material_cost numeric(10,2) DEFAULT 0.0,
    total_labor_cost numeric(10,2) DEFAULT 0.0,
    total_external_cost numeric(10,2) DEFAULT 0.0,
    maintenance_request_origin_id integer,
    CONSTRAINT check_section_global CHECK ((((format_change_type)::text = 'Global'::text) OR (section_id IS NOT NULL))),
    CONSTRAINT check_section_global_format CHECK (((((format_change_type)::text = ANY ((ARRAY['Individual'::character varying, 'Línea'::character varying])::text[])) AND (section_id IS NOT NULL)) OR ((format_change_type)::text = 'Global'::text) OR ((format_change_type IS NULL) AND (section_id IS NOT NULL)))),
    CONSTRAINT valid_status CHECK (((status)::text = ANY ((ARRAY['Pendiente'::character varying, 'En curso'::character varying, 'En revisión'::character varying, 'Cerrada'::character varying])::text[]))),
    CONSTRAINT valid_work_type CHECK (((work_type)::text = ANY ((ARRAY['Preventivo'::character varying, 'Correctivo'::character varying, 'Inspección'::character varying, 'Mejora'::character varying, 'Modificación'::character varying, 'Seguridad'::character varying, 'Cambio de Formato'::character varying, 'Setup de Línea'::character varying, 'Cambio Global de Planta'::character varying])::text[]))),
    CONSTRAINT work_orders_format_change_type_check CHECK (((format_change_type)::text = ANY ((ARRAY['Individual'::character varying, 'Línea'::character varying, 'Global'::character varying])::text[])))
);


--
-- Name: COLUMN work_orders.format_change_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.work_orders.format_change_type IS 'Tipo de cambio: Individual, Línea, Global';


--
-- Name: COLUMN work_orders.affected_machines; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.work_orders.affected_machines IS 'JSON con IDs de máquinas afectadas en el cambio';


--
-- Name: COLUMN work_orders.format_from_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.work_orders.format_from_id IS 'ID del formato origen (FK a formats)';


--
-- Name: COLUMN work_orders.format_to_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.work_orders.format_to_id IS 'ID del formato destino (FK a formats)';


--
-- Name: COLUMN work_orders.format_from_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.work_orders.format_from_name IS 'Nombre del formato origen si no está catalogado';


--
-- Name: COLUMN work_orders.format_to_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.work_orders.format_to_name IS 'Nombre del formato destino si no está catalogado';


--
-- Name: COLUMN work_orders.setup_duration; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.work_orders.setup_duration IS 'Tiempo real de setup en horas';


--
-- Name: COLUMN work_orders.estimated_setup_duration; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.work_orders.estimated_setup_duration IS 'Tiempo estimado de setup en horas';


--
-- Name: COLUMN work_orders.production_loss_hours; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.work_orders.production_loss_hours IS 'Horas de producción perdidas durante el cambio';


--
-- Name: COLUMN work_orders.setup_team; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.work_orders.setup_team IS 'JSON con IDs de usuarios del equipo de setup';


--
-- Name: COLUMN work_orders.setup_notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.work_orders.setup_notes IS 'Notas específicas del setup y cambio de formato';


--
-- Name: work_orders_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: work_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.work_orders_id_seq OWNED BY public.work_orders.id;


--
-- Name: absences id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.absences ALTER COLUMN id SET DEFAULT nextval('public.absences_id_seq'::regclass);


--
-- Name: achievements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.achievements ALTER COLUMN id SET DEFAULT nextval('public.achievements_id_seq'::regclass);


--
-- Name: ai_configuration id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_configuration ALTER COLUMN id SET DEFAULT nextval('public.ai_configuration_id_seq'::regclass);


--
-- Name: ai_model_performance id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_model_performance ALTER COLUMN id SET DEFAULT nextval('public.ai_model_performance_id_seq'::regclass);


--
-- Name: alerts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts ALTER COLUMN id SET DEFAULT nextval('public.alerts_id_seq'::regclass);


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: cause_codes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cause_codes ALTER COLUMN id SET DEFAULT nextval('public.cause_codes_id_seq'::regclass);


--
-- Name: challenge_participations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.challenge_participations ALTER COLUMN id SET DEFAULT nextval('public.challenge_participations_id_seq'::regclass);


--
-- Name: challenges id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.challenges ALTER COLUMN id SET DEFAULT nextval('public.challenges_id_seq'::regclass);


--
-- Name: checklist_progress id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.checklist_progress ALTER COLUMN id SET DEFAULT nextval('public.checklist_progress_id_seq'::regclass);


--
-- Name: communication_reads id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.communication_reads ALTER COLUMN id SET DEFAULT nextval('public.communication_reads_id_seq'::regclass);


--
-- Name: communications id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.communications ALTER COLUMN id SET DEFAULT nextval('public.communications_id_seq'::regclass);


--
-- Name: document_attachments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_attachments ALTER COLUMN id SET DEFAULT nextval('public.document_attachments_id_seq'::regclass);


--
-- Name: documents id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents ALTER COLUMN id SET DEFAULT nextval('public.documents_id_seq'::regclass);


--
-- Name: failure_codes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.failure_codes ALTER COLUMN id SET DEFAULT nextval('public.failure_codes_id_seq'::regclass);


--
-- Name: failure_patterns id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.failure_patterns ALTER COLUMN id SET DEFAULT nextval('public.failure_patterns_id_seq'::regclass);


--
-- Name: formats id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.formats ALTER COLUMN id SET DEFAULT nextval('public.formats_id_seq'::regclass);


--
-- Name: inventory id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory ALTER COLUMN id SET DEFAULT nextval('public.inventory_id_seq'::regclass);


--
-- Name: lines id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lines ALTER COLUMN id SET DEFAULT nextval('public.lines_id_seq'::regclass);


--
-- Name: machine_predictions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.machine_predictions ALTER COLUMN id SET DEFAULT nextval('public.machine_predictions_id_seq'::regclass);


--
-- Name: machines id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.machines ALTER COLUMN id SET DEFAULT nextval('public.machines_id_seq'::regclass);


--
-- Name: maintenance_backlogs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_backlogs ALTER COLUMN id SET DEFAULT nextval('public.maintenance_backlogs_id_seq'::regclass);


--
-- Name: maintenance_optimizations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_optimizations ALTER COLUMN id SET DEFAULT nextval('public.maintenance_optimizations_id_seq'::regclass);


--
-- Name: maintenance_requests id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_requests ALTER COLUMN id SET DEFAULT nextval('public.maintenance_requests_id_seq'::regclass);


--
-- Name: maintenances id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenances ALTER COLUMN id SET DEFAULT nextval('public.maintenances_id_seq'::regclass);


--
-- Name: point_transactions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.point_transactions ALTER COLUMN id SET DEFAULT nextval('public.point_transactions_id_seq'::regclass);


--
-- Name: remedy_codes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.remedy_codes ALTER COLUMN id SET DEFAULT nextval('public.remedy_codes_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: sections id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sections ALTER COLUMN id SET DEFAULT nextval('public.sections_id_seq'::regclass);


--
-- Name: shift_assignments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_assignments ALTER COLUMN id SET DEFAULT nextval('public.shift_assignments_id_seq'::regclass);


--
-- Name: shift_overrides id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_overrides ALTER COLUMN id SET DEFAULT nextval('public.shift_overrides_id_seq'::regclass);


--
-- Name: shift_patterns id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_patterns ALTER COLUMN id SET DEFAULT nextval('public.shift_patterns_id_seq'::regclass);


--
-- Name: supplier_product_prices id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_product_prices ALTER COLUMN id SET DEFAULT nextval('public.supplier_product_prices_id_seq'::regclass);


--
-- Name: suppliers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.suppliers ALTER COLUMN id SET DEFAULT nextval('public.suppliers_id_seq'::regclass);


--
-- Name: task_lists id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_lists ALTER COLUMN id SET DEFAULT nextval('public.task_lists_id_seq'::regclass);


--
-- Name: task_steps id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_steps ALTER COLUMN id SET DEFAULT nextval('public.task_steps_id_seq'::regclass);


--
-- Name: user_achievements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_achievements ALTER COLUMN id SET DEFAULT nextval('public.user_achievements_id_seq'::regclass);


--
-- Name: user_points id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_points ALTER COLUMN id SET DEFAULT nextval('public.user_points_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: vacation_requests id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacation_requests ALTER COLUMN id SET DEFAULT nextval('public.vacation_requests_id_seq'::regclass);


--
-- Name: warehouses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warehouses ALTER COLUMN id SET DEFAULT nextval('public.warehouses_id_seq'::regclass);


--
-- Name: work_order_materials id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_order_materials ALTER COLUMN id SET DEFAULT nextval('public.work_order_materials_id_seq'::regclass);


--
-- Name: work_order_technicians id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_order_technicians ALTER COLUMN id SET DEFAULT nextval('public.work_order_technicians_id_seq'::regclass);


--
-- Name: work_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders ALTER COLUMN id SET DEFAULT nextval('public.work_orders_id_seq'::regclass);


--
-- Name: absences absences_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.absences
    ADD CONSTRAINT absences_pkey PRIMARY KEY (id);


--
-- Name: achievements achievements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.achievements
    ADD CONSTRAINT achievements_pkey PRIMARY KEY (id);


--
-- Name: ai_configuration ai_configuration_config_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_configuration
    ADD CONSTRAINT ai_configuration_config_key_key UNIQUE (config_key);


--
-- Name: ai_configuration ai_configuration_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_configuration
    ADD CONSTRAINT ai_configuration_pkey PRIMARY KEY (id);


--
-- Name: ai_model_performance ai_model_performance_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_model_performance
    ADD CONSTRAINT ai_model_performance_pkey PRIMARY KEY (id);


--
-- Name: alert_user alert_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_user
    ADD CONSTRAINT alert_user_pkey PRIMARY KEY (alert_id, user_id);


--
-- Name: alerts alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: cause_codes cause_codes_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cause_codes
    ADD CONSTRAINT cause_codes_code_key UNIQUE (code);


--
-- Name: cause_codes cause_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cause_codes
    ADD CONSTRAINT cause_codes_pkey PRIMARY KEY (id);


--
-- Name: challenge_participations challenge_participations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.challenge_participations
    ADD CONSTRAINT challenge_participations_pkey PRIMARY KEY (id);


--
-- Name: challenges challenges_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.challenges
    ADD CONSTRAINT challenges_pkey PRIMARY KEY (id);


--
-- Name: checklist_progress checklist_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.checklist_progress
    ADD CONSTRAINT checklist_progress_pkey PRIMARY KEY (id);


--
-- Name: communication_reads communication_reads_communication_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.communication_reads
    ADD CONSTRAINT communication_reads_communication_id_user_id_key UNIQUE (communication_id, user_id);


--
-- Name: communication_reads communication_reads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.communication_reads
    ADD CONSTRAINT communication_reads_pkey PRIMARY KEY (id);


--
-- Name: communications communications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.communications
    ADD CONSTRAINT communications_pkey PRIMARY KEY (id);


--
-- Name: document_attachments document_attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_attachments
    ADD CONSTRAINT document_attachments_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: failure_codes failure_codes_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.failure_codes
    ADD CONSTRAINT failure_codes_code_key UNIQUE (code);


--
-- Name: failure_codes failure_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.failure_codes
    ADD CONSTRAINT failure_codes_pkey PRIMARY KEY (id);


--
-- Name: failure_patterns failure_patterns_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.failure_patterns
    ADD CONSTRAINT failure_patterns_pkey PRIMARY KEY (id);


--
-- Name: formats formats_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.formats
    ADD CONSTRAINT formats_name_key UNIQUE (name);


--
-- Name: formats formats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.formats
    ADD CONSTRAINT formats_pkey PRIMARY KEY (id);


--
-- Name: inventory inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_pkey PRIMARY KEY (id);


--
-- Name: lines lines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lines
    ADD CONSTRAINT lines_pkey PRIMARY KEY (id);


--
-- Name: machine_parts_association machine_parts_association_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.machine_parts_association
    ADD CONSTRAINT machine_parts_association_pkey PRIMARY KEY (machine_id, inventory_id);


--
-- Name: machine_predictions machine_predictions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.machine_predictions
    ADD CONSTRAINT machine_predictions_pkey PRIMARY KEY (id);


--
-- Name: machines machines_numero_serie_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.machines
    ADD CONSTRAINT machines_numero_serie_key UNIQUE (numero_serie);


--
-- Name: machines machines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.machines
    ADD CONSTRAINT machines_pkey PRIMARY KEY (id);


--
-- Name: maintenance_backlogs maintenance_backlogs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_backlogs
    ADD CONSTRAINT maintenance_backlogs_pkey PRIMARY KEY (id);


--
-- Name: maintenance_optimizations maintenance_optimizations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_optimizations
    ADD CONSTRAINT maintenance_optimizations_pkey PRIMARY KEY (id);


--
-- Name: maintenance_requests maintenance_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_requests
    ADD CONSTRAINT maintenance_requests_pkey PRIMARY KEY (id);


--
-- Name: maintenances maintenances_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenances
    ADD CONSTRAINT maintenances_pkey PRIMARY KEY (id);


--
-- Name: point_transactions point_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.point_transactions
    ADD CONSTRAINT point_transactions_pkey PRIMARY KEY (id);


--
-- Name: remedy_codes remedy_codes_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.remedy_codes
    ADD CONSTRAINT remedy_codes_code_key UNIQUE (code);


--
-- Name: remedy_codes remedy_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.remedy_codes
    ADD CONSTRAINT remedy_codes_pkey PRIMARY KEY (id);


--
-- Name: roles roles_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_nombre_key UNIQUE (nombre);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: sections sections_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sections
    ADD CONSTRAINT sections_nombre_key UNIQUE (nombre);


--
-- Name: sections sections_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sections
    ADD CONSTRAINT sections_pkey PRIMARY KEY (id);


--
-- Name: shift_assignments shift_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_assignments
    ADD CONSTRAINT shift_assignments_pkey PRIMARY KEY (id);


--
-- Name: shift_assignments shift_assignments_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_assignments
    ADD CONSTRAINT shift_assignments_user_id_key UNIQUE (user_id);


--
-- Name: shift_overrides shift_overrides_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_overrides
    ADD CONSTRAINT shift_overrides_pkey PRIMARY KEY (id);


--
-- Name: shift_patterns shift_patterns_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_patterns
    ADD CONSTRAINT shift_patterns_pkey PRIMARY KEY (id);


--
-- Name: supplier_product_prices supplier_product_prices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_product_prices
    ADD CONSTRAINT supplier_product_prices_pkey PRIMARY KEY (id);


--
-- Name: suppliers suppliers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.suppliers
    ADD CONSTRAINT suppliers_pkey PRIMARY KEY (id);


--
-- Name: task_lists task_lists_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_lists
    ADD CONSTRAINT task_lists_pkey PRIMARY KEY (id);


--
-- Name: task_steps task_steps_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_steps
    ADD CONSTRAINT task_steps_pkey PRIMARY KEY (id);


--
-- Name: user_achievements user_achievements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_achievements
    ADD CONSTRAINT user_achievements_pkey PRIMARY KEY (id);


--
-- Name: user_points user_points_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_points
    ADD CONSTRAINT user_points_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: vacation_requests vacation_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacation_requests
    ADD CONSTRAINT vacation_requests_pkey PRIMARY KEY (id);


--
-- Name: warehouses warehouses_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warehouses
    ADD CONSTRAINT warehouses_name_key UNIQUE (name);


--
-- Name: warehouses warehouses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warehouses
    ADD CONSTRAINT warehouses_pkey PRIMARY KEY (id);


--
-- Name: work_order_materials work_order_materials_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_order_materials
    ADD CONSTRAINT work_order_materials_pkey PRIMARY KEY (id);


--
-- Name: work_order_technicians work_order_technicians_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_order_technicians
    ADD CONSTRAINT work_order_technicians_pkey PRIMARY KEY (id);


--
-- Name: work_order_technicians work_order_technicians_work_order_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_order_technicians
    ADD CONSTRAINT work_order_technicians_work_order_id_user_id_key UNIQUE (work_order_id, user_id);


--
-- Name: work_orders work_orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT work_orders_order_number_key UNIQUE (order_number);


--
-- Name: work_orders work_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT work_orders_pkey PRIMARY KEY (id);


--
-- Name: idx_ai_configuration_key; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_configuration_key ON public.ai_configuration USING btree (config_key);


--
-- Name: idx_ai_configuration_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_configuration_type ON public.ai_configuration USING btree (config_type);


--
-- Name: idx_ai_model_performance_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_model_performance_model ON public.ai_model_performance USING btree (model_name);


--
-- Name: idx_ai_model_performance_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_model_performance_period ON public.ai_model_performance USING btree (evaluation_period_start, evaluation_period_end);


--
-- Name: idx_ai_model_performance_updated; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_model_performance_updated ON public.ai_model_performance USING btree (last_updated);


--
-- Name: idx_audit_logs_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_action ON public.audit_logs USING btree (action);


--
-- Name: idx_audit_logs_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_entity ON public.audit_logs USING btree (entity_type, entity_id);


--
-- Name: idx_audit_logs_module; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_module ON public.audit_logs USING btree (module);


--
-- Name: idx_audit_logs_severity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_severity ON public.audit_logs USING btree (severity);


--
-- Name: idx_audit_logs_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_timestamp ON public.audit_logs USING btree ("timestamp");


--
-- Name: idx_audit_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_user_id ON public.audit_logs USING btree (user_id);


--
-- Name: idx_checklist_progress_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_checklist_progress_created_at ON public.checklist_progress USING btree (created_at);


--
-- Name: idx_checklist_progress_created_by_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_checklist_progress_created_by_id ON public.checklist_progress USING btree (created_by_id);


--
-- Name: idx_checklist_progress_is_completed; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_checklist_progress_is_completed ON public.checklist_progress USING btree (is_completed);


--
-- Name: idx_checklist_progress_task_list_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_checklist_progress_task_list_id ON public.checklist_progress USING btree (task_list_id);


--
-- Name: idx_checklist_progress_wo_tl_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_checklist_progress_wo_tl_unique ON public.checklist_progress USING btree (work_order_id, task_list_id);


--
-- Name: idx_checklist_progress_work_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_checklist_progress_work_order_id ON public.checklist_progress USING btree (work_order_id);


--
-- Name: idx_communication_reads_comm_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_communication_reads_comm_user ON public.communication_reads USING btree (communication_id, user_id);


--
-- Name: idx_communications_assigned_to; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_communications_assigned_to ON public.communications USING btree (assigned_to_id);


--
-- Name: idx_communications_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_communications_created_at ON public.communications USING btree (created_at);


--
-- Name: idx_communications_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_communications_created_by ON public.communications USING btree (created_by_id);


--
-- Name: idx_communications_direction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_communications_direction ON public.communications USING btree (direction);


--
-- Name: idx_communications_machine; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_communications_machine ON public.communications USING btree (machine_id);


--
-- Name: idx_communications_parent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_communications_parent ON public.communications USING btree (parent_communication_id);


--
-- Name: idx_communications_priority; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_communications_priority ON public.communications USING btree (priority);


--
-- Name: idx_communications_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_communications_status ON public.communications USING btree (status);


--
-- Name: idx_communications_target_department; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_communications_target_department ON public.communications USING btree (target_department);


--
-- Name: idx_communications_target_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_communications_target_role ON public.communications USING btree (target_role_id);


--
-- Name: idx_communications_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_communications_type ON public.communications USING btree (type);


--
-- Name: idx_failure_patterns_confidence; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_failure_patterns_confidence ON public.failure_patterns USING btree (confidence_score);


--
-- Name: idx_failure_patterns_discovered_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_failure_patterns_discovered_at ON public.failure_patterns USING btree (discovered_at);


--
-- Name: idx_failure_patterns_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_failure_patterns_status ON public.failure_patterns USING btree (status);


--
-- Name: idx_formats_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_formats_active ON public.formats USING btree (active);


--
-- Name: idx_formats_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_formats_created_at ON public.formats USING btree (created_at);


--
-- Name: idx_formats_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_formats_name ON public.formats USING btree (name);


--
-- Name: idx_inventory_tipo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_inventory_tipo ON public.inventory USING btree (tipo);


--
-- Name: idx_machine_predictions_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_machine_predictions_created_at ON public.machine_predictions USING btree (created_at);


--
-- Name: idx_machine_predictions_machine_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_machine_predictions_machine_id ON public.machine_predictions USING btree (machine_id);


--
-- Name: idx_machine_predictions_predicted_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_machine_predictions_predicted_date ON public.machine_predictions USING btree (predicted_date);


--
-- Name: idx_machine_predictions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_machine_predictions_status ON public.machine_predictions USING btree (status);


--
-- Name: idx_maintenance_optimizations_generated_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_maintenance_optimizations_generated_at ON public.maintenance_optimizations USING btree (generated_at);


--
-- Name: idx_maintenance_optimizations_section_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_maintenance_optimizations_section_id ON public.maintenance_optimizations USING btree (section_id);


--
-- Name: idx_maintenance_optimizations_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_maintenance_optimizations_status ON public.maintenance_optimizations USING btree (status);


--
-- Name: idx_maintenances_legal_composite; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_maintenances_legal_composite ON public.maintenances USING btree (type, tipo_regulacion) WHERE ((type)::text = 'Legal'::text);


--
-- Name: idx_maintenances_numero_certificado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_maintenances_numero_certificado ON public.maintenances USING btree (numero_certificado);


--
-- Name: idx_maintenances_organismo_certificador; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_maintenances_organismo_certificador ON public.maintenances USING btree (organismo_certificador);


--
-- Name: idx_maintenances_task_list_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_maintenances_task_list_id ON public.maintenances USING btree (task_list_id);


--
-- Name: idx_maintenances_tipo_regulacion; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_maintenances_tipo_regulacion ON public.maintenances USING btree (tipo_regulacion);


--
-- Name: idx_work_order_technicians_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_work_order_technicians_active ON public.work_order_technicians USING btree (is_active);


--
-- Name: idx_work_order_technicians_assigned_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_work_order_technicians_assigned_at ON public.work_order_technicians USING btree (assigned_at);


--
-- Name: idx_work_order_technicians_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_work_order_technicians_role ON public.work_order_technicians USING btree (role);


--
-- Name: idx_work_order_technicians_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_work_order_technicians_user_id ON public.work_order_technicians USING btree (user_id);


--
-- Name: idx_work_order_technicians_work_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_work_order_technicians_work_order_id ON public.work_order_technicians USING btree (work_order_id);


--
-- Name: idx_work_orders_format_change_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_work_orders_format_change_type ON public.work_orders USING btree (format_change_type);


--
-- Name: idx_work_orders_format_from; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_work_orders_format_from ON public.work_orders USING btree (format_from_id);


--
-- Name: idx_work_orders_format_from_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_work_orders_format_from_id ON public.work_orders USING btree (format_from_id);


--
-- Name: idx_work_orders_format_to; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_work_orders_format_to ON public.work_orders USING btree (format_to_id);


--
-- Name: idx_work_orders_format_to_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_work_orders_format_to_id ON public.work_orders USING btree (format_to_id);


--
-- Name: idx_work_orders_generated_from_maintenance; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_work_orders_generated_from_maintenance ON public.work_orders USING btree (generated_from_maintenance_id, status);


--
-- Name: idx_work_orders_setup_duration; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_work_orders_setup_duration ON public.work_orders USING btree (setup_duration);


--
-- Name: ix_absences_absence_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_absences_absence_type ON public.absences USING btree (absence_type);


--
-- Name: ix_absences_end_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_absences_end_date ON public.absences USING btree (end_date);


--
-- Name: ix_absences_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_absences_id ON public.absences USING btree (id);


--
-- Name: ix_absences_start_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_absences_start_date ON public.absences USING btree (start_date);


--
-- Name: ix_absences_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_absences_user_id ON public.absences USING btree (user_id);


--
-- Name: ix_achievements_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_achievements_id ON public.achievements USING btree (id);


--
-- Name: ix_alerts_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_alerts_type ON public.alerts USING btree (type);


--
-- Name: ix_cause_codes_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cause_codes_id ON public.cause_codes USING btree (id);


--
-- Name: ix_challenge_participations_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_challenge_participations_id ON public.challenge_participations USING btree (id);


--
-- Name: ix_challenges_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_challenges_id ON public.challenges USING btree (id);


--
-- Name: ix_documents_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_documents_id ON public.documents USING btree (id);


--
-- Name: ix_failure_codes_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_failure_codes_id ON public.failure_codes USING btree (id);


--
-- Name: ix_machines_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_machines_id ON public.machines USING btree (id);


--
-- Name: ix_maintenances_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_maintenances_id ON public.maintenances USING btree (id);


--
-- Name: ix_point_transactions_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_point_transactions_id ON public.point_transactions USING btree (id);


--
-- Name: ix_remedy_codes_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_remedy_codes_id ON public.remedy_codes USING btree (id);


--
-- Name: ix_roles_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_roles_id ON public.roles USING btree (id);


--
-- Name: ix_sections_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sections_id ON public.sections USING btree (id);


--
-- Name: ix_shift_assignments_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_shift_assignments_id ON public.shift_assignments USING btree (id);


--
-- Name: ix_shift_overrides_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_shift_overrides_date ON public.shift_overrides USING btree (date);


--
-- Name: ix_shift_overrides_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_shift_overrides_id ON public.shift_overrides USING btree (id);


--
-- Name: ix_shift_overrides_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_shift_overrides_user_id ON public.shift_overrides USING btree (user_id);


--
-- Name: ix_shift_patterns_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_shift_patterns_id ON public.shift_patterns USING btree (id);


--
-- Name: ix_shift_patterns_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_shift_patterns_name ON public.shift_patterns USING btree (name);


--
-- Name: ix_supplier_product_prices_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_supplier_product_prices_id ON public.supplier_product_prices USING btree (id);


--
-- Name: ix_supplier_product_prices_product_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_supplier_product_prices_product_name ON public.supplier_product_prices USING btree (product_name);


--
-- Name: ix_supplier_product_prices_supplier_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_supplier_product_prices_supplier_id ON public.supplier_product_prices USING btree (supplier_id);


--
-- Name: ix_suppliers_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_suppliers_id ON public.suppliers USING btree (id);


--
-- Name: ix_task_lists_applies_to_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_task_lists_applies_to_type ON public.task_lists USING btree (applies_to_type);


--
-- Name: ix_task_lists_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_task_lists_id ON public.task_lists USING btree (id);


--
-- Name: ix_task_lists_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_task_lists_name ON public.task_lists USING btree (name);


--
-- Name: ix_task_steps_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_task_steps_id ON public.task_steps USING btree (id);


--
-- Name: ix_user_achievements_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_achievements_id ON public.user_achievements USING btree (id);


--
-- Name: ix_user_points_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_points_id ON public.user_points USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: ix_vacation_requests_end_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_vacation_requests_end_date ON public.vacation_requests USING btree (end_date);


--
-- Name: ix_vacation_requests_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_vacation_requests_id ON public.vacation_requests USING btree (id);


--
-- Name: ix_vacation_requests_start_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_vacation_requests_start_date ON public.vacation_requests USING btree (start_date);


--
-- Name: ix_vacation_requests_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_vacation_requests_status ON public.vacation_requests USING btree (status);


--
-- Name: ix_vacation_requests_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_vacation_requests_user_id ON public.vacation_requests USING btree (user_id);


--
-- Name: ix_work_orders_generated_from_maintenance_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_work_orders_generated_from_maintenance_id ON public.work_orders USING btree (generated_from_maintenance_id);


--
-- Name: ix_work_orders_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_work_orders_id ON public.work_orders USING btree (id);


--
-- Name: ai_configuration trigger_ai_config_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_ai_config_updated_at BEFORE UPDATE ON public.ai_configuration FOR EACH ROW EXECUTE FUNCTION public.update_ai_config_timestamp();


--
-- Name: checklist_progress trigger_checklist_progress_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_checklist_progress_updated_at BEFORE UPDATE ON public.checklist_progress FOR EACH ROW EXECUTE FUNCTION public.update_checklist_progress_updated_at();


--
-- Name: checklist_progress trigger_update_checklist_progress_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_checklist_progress_updated_at BEFORE UPDATE ON public.checklist_progress FOR EACH ROW EXECUTE FUNCTION public.update_checklist_progress_updated_at();


--
-- Name: absences absences_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.absences
    ADD CONSTRAINT absences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: ai_configuration ai_configuration_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_configuration
    ADD CONSTRAINT ai_configuration_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(id);


--
-- Name: alert_user alert_user_alert_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_user
    ADD CONSTRAINT alert_user_alert_id_fkey FOREIGN KEY (alert_id) REFERENCES public.alerts(id);


--
-- Name: alert_user alert_user_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_user
    ADD CONSTRAINT alert_user_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: alerts alerts_resolved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_resolved_by_id_fkey FOREIGN KEY (resolved_by_id) REFERENCES public.users(id);


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: challenge_participations challenge_participations_challenge_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.challenge_participations
    ADD CONSTRAINT challenge_participations_challenge_id_fkey FOREIGN KEY (challenge_id) REFERENCES public.challenges(id);


--
-- Name: challenge_participations challenge_participations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.challenge_participations
    ADD CONSTRAINT challenge_participations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: challenges challenges_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.challenges
    ADD CONSTRAINT challenges_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- Name: communication_reads communication_reads_communication_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.communication_reads
    ADD CONSTRAINT communication_reads_communication_id_fkey FOREIGN KEY (communication_id) REFERENCES public.communications(id) ON DELETE CASCADE;


--
-- Name: communication_reads communication_reads_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.communication_reads
    ADD CONSTRAINT communication_reads_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: communications communications_assigned_to_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.communications
    ADD CONSTRAINT communications_assigned_to_id_fkey FOREIGN KEY (assigned_to_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: communications communications_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.communications
    ADD CONSTRAINT communications_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: communications communications_machine_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.communications
    ADD CONSTRAINT communications_machine_id_fkey FOREIGN KEY (machine_id) REFERENCES public.machines(id) ON DELETE SET NULL;


--
-- Name: document_attachments document_attachments_uploaded_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_attachments
    ADD CONSTRAINT document_attachments_uploaded_by_id_fkey FOREIGN KEY (uploaded_by_id) REFERENCES public.users(id);


--
-- Name: documents documents_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- Name: failure_patterns failure_patterns_discovered_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.failure_patterns
    ADD CONSTRAINT failure_patterns_discovered_by_id_fkey FOREIGN KEY (discovered_by_id) REFERENCES public.users(id);


--
-- Name: checklist_progress fk_checklist_progress_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.checklist_progress
    ADD CONSTRAINT fk_checklist_progress_created_by FOREIGN KEY (created_by_id) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: checklist_progress fk_checklist_progress_task_list; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.checklist_progress
    ADD CONSTRAINT fk_checklist_progress_task_list FOREIGN KEY (task_list_id) REFERENCES public.task_lists(id) ON DELETE CASCADE;


--
-- Name: checklist_progress fk_checklist_progress_work_order; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.checklist_progress
    ADD CONSTRAINT fk_checklist_progress_work_order FOREIGN KEY (work_order_id) REFERENCES public.work_orders(id) ON DELETE CASCADE;


--
-- Name: communications fk_communications_parent; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.communications
    ADD CONSTRAINT fk_communications_parent FOREIGN KEY (parent_communication_id) REFERENCES public.communications(id);


--
-- Name: communications fk_communications_target_role; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.communications
    ADD CONSTRAINT fk_communications_target_role FOREIGN KEY (target_role_id) REFERENCES public.roles(id);


--
-- Name: inventory fk_inventory_warehouse; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT fk_inventory_warehouse FOREIGN KEY (warehouse_id) REFERENCES public.warehouses(id);


--
-- Name: task_lists fk_task_lists_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_lists
    ADD CONSTRAINT fk_task_lists_created_by FOREIGN KEY (created_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: work_orders fk_work_orders_cause_code; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT fk_work_orders_cause_code FOREIGN KEY (cause_code_id) REFERENCES public.cause_codes(id);


--
-- Name: work_orders fk_work_orders_document; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT fk_work_orders_document FOREIGN KEY (source_document_id) REFERENCES public.documents(id);


--
-- Name: work_orders fk_work_orders_failure_code; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT fk_work_orders_failure_code FOREIGN KEY (failure_code_id) REFERENCES public.failure_codes(id);


--
-- Name: work_orders fk_work_orders_format_from; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT fk_work_orders_format_from FOREIGN KEY (format_from_id) REFERENCES public.formats(id) ON DELETE SET NULL;


--
-- Name: work_orders fk_work_orders_format_to; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT fk_work_orders_format_to FOREIGN KEY (format_to_id) REFERENCES public.formats(id) ON DELETE SET NULL;


--
-- Name: work_orders fk_work_orders_maintenance; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT fk_work_orders_maintenance FOREIGN KEY (generated_from_maintenance_id) REFERENCES public.maintenances(id);


--
-- Name: work_orders fk_work_orders_remedy_code; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT fk_work_orders_remedy_code FOREIGN KEY (remedy_code_id) REFERENCES public.remedy_codes(id);


--
-- Name: work_orders fk_work_orders_task_list; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT fk_work_orders_task_list FOREIGN KEY (task_list_id) REFERENCES public.task_lists(id);


--
-- Name: inventory inventory_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id);


--
-- Name: lines lines_section_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lines
    ADD CONSTRAINT lines_section_id_fkey FOREIGN KEY (section_id) REFERENCES public.sections(id);


--
-- Name: machine_parts_association machine_parts_association_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.machine_parts_association
    ADD CONSTRAINT machine_parts_association_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventory(id) ON DELETE CASCADE;


--
-- Name: machine_parts_association machine_parts_association_machine_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.machine_parts_association
    ADD CONSTRAINT machine_parts_association_machine_id_fkey FOREIGN KEY (machine_id) REFERENCES public.machines(id) ON DELETE CASCADE;


--
-- Name: machine_predictions machine_predictions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.machine_predictions
    ADD CONSTRAINT machine_predictions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- Name: machine_predictions machine_predictions_machine_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.machine_predictions
    ADD CONSTRAINT machine_predictions_machine_id_fkey FOREIGN KEY (machine_id) REFERENCES public.machines(id) ON DELETE CASCADE;


--
-- Name: machines machines_line_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.machines
    ADD CONSTRAINT machines_line_id_fkey FOREIGN KEY (line_id) REFERENCES public.lines(id);


--
-- Name: machines machines_section_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.machines
    ADD CONSTRAINT machines_section_id_fkey FOREIGN KEY (section_id) REFERENCES public.sections(id);


--
-- Name: maintenance_backlogs maintenance_backlogs_actual_work_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_backlogs
    ADD CONSTRAINT maintenance_backlogs_actual_work_order_id_fkey FOREIGN KEY (actual_work_order_id) REFERENCES public.work_orders(id);


--
-- Name: maintenance_backlogs maintenance_backlogs_assigned_to_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_backlogs
    ADD CONSTRAINT maintenance_backlogs_assigned_to_id_fkey FOREIGN KEY (assigned_to_id) REFERENCES public.users(id);


--
-- Name: maintenance_backlogs maintenance_backlogs_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_backlogs
    ADD CONSTRAINT maintenance_backlogs_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- Name: maintenance_backlogs maintenance_backlogs_machine_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_backlogs
    ADD CONSTRAINT maintenance_backlogs_machine_id_fkey FOREIGN KEY (machine_id) REFERENCES public.machines(id);


--
-- Name: maintenance_backlogs maintenance_backlogs_section_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_backlogs
    ADD CONSTRAINT maintenance_backlogs_section_id_fkey FOREIGN KEY (section_id) REFERENCES public.sections(id);


--
-- Name: maintenance_optimizations maintenance_optimizations_generated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_optimizations
    ADD CONSTRAINT maintenance_optimizations_generated_by_id_fkey FOREIGN KEY (generated_by_id) REFERENCES public.users(id);


--
-- Name: maintenance_optimizations maintenance_optimizations_section_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_optimizations
    ADD CONSTRAINT maintenance_optimizations_section_id_fkey FOREIGN KEY (section_id) REFERENCES public.sections(id) ON DELETE SET NULL;


--
-- Name: maintenance_requests maintenance_requests_machine_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_requests
    ADD CONSTRAINT maintenance_requests_machine_id_fkey FOREIGN KEY (machine_id) REFERENCES public.machines(id);


--
-- Name: maintenance_requests maintenance_requests_reported_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_requests
    ADD CONSTRAINT maintenance_requests_reported_by_id_fkey FOREIGN KEY (reported_by_id) REFERENCES public.users(id);


--
-- Name: maintenance_requests maintenance_requests_reviewed_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_requests
    ADD CONSTRAINT maintenance_requests_reviewed_by_id_fkey FOREIGN KEY (reviewed_by_id) REFERENCES public.users(id);


--
-- Name: maintenance_requests maintenance_requests_work_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_requests
    ADD CONSTRAINT maintenance_requests_work_order_id_fkey FOREIGN KEY (work_order_id) REFERENCES public.work_orders(id);


--
-- Name: maintenances maintenances_assigned_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenances
    ADD CONSTRAINT maintenances_assigned_role_id_fkey FOREIGN KEY (assigned_role_id) REFERENCES public.roles(id);


--
-- Name: maintenances maintenances_assigned_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenances
    ADD CONSTRAINT maintenances_assigned_user_id_fkey FOREIGN KEY (assigned_user_id) REFERENCES public.users(id);


--
-- Name: maintenances maintenances_machine_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenances
    ADD CONSTRAINT maintenances_machine_id_fkey FOREIGN KEY (machine_id) REFERENCES public.machines(id);


--
-- Name: maintenances maintenances_task_list_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenances
    ADD CONSTRAINT maintenances_task_list_id_fkey FOREIGN KEY (task_list_id) REFERENCES public.task_lists(id);


--
-- Name: point_transactions point_transactions_user_points_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.point_transactions
    ADD CONSTRAINT point_transactions_user_points_id_fkey FOREIGN KEY (user_points_id) REFERENCES public.user_points(id);


--
-- Name: shift_assignments shift_assignments_pattern_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_assignments
    ADD CONSTRAINT shift_assignments_pattern_id_fkey FOREIGN KEY (pattern_id) REFERENCES public.shift_patterns(id);


--
-- Name: shift_assignments shift_assignments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_assignments
    ADD CONSTRAINT shift_assignments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: shift_overrides shift_overrides_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_overrides
    ADD CONSTRAINT shift_overrides_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: supplier_product_prices supplier_product_prices_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_product_prices
    ADD CONSTRAINT supplier_product_prices_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id);


--
-- Name: supplier_product_prices supplier_product_prices_warehouse_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_product_prices
    ADD CONSTRAINT supplier_product_prices_warehouse_id_fkey FOREIGN KEY (warehouse_id) REFERENCES public.warehouses(id);


--
-- Name: task_steps task_steps_task_list_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_steps
    ADD CONSTRAINT task_steps_task_list_id_fkey FOREIGN KEY (task_list_id) REFERENCES public.task_lists(id) ON DELETE CASCADE;


--
-- Name: user_achievements user_achievements_achievement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_achievements
    ADD CONSTRAINT user_achievements_achievement_id_fkey FOREIGN KEY (achievement_id) REFERENCES public.achievements(id);


--
-- Name: user_achievements user_achievements_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_achievements
    ADD CONSTRAINT user_achievements_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_points user_points_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_points
    ADD CONSTRAINT user_points_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: users users_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- Name: users users_section_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_section_id_fkey FOREIGN KEY (section_id) REFERENCES public.sections(id);


--
-- Name: vacation_requests vacation_requests_reviewed_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacation_requests
    ADD CONSTRAINT vacation_requests_reviewed_by_id_fkey FOREIGN KEY (reviewed_by_id) REFERENCES public.users(id);


--
-- Name: vacation_requests vacation_requests_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacation_requests
    ADD CONSTRAINT vacation_requests_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: work_order_materials work_order_materials_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_order_materials
    ADD CONSTRAINT work_order_materials_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventory(id) ON DELETE RESTRICT;


--
-- Name: work_order_materials work_order_materials_work_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_order_materials
    ADD CONSTRAINT work_order_materials_work_order_id_fkey FOREIGN KEY (work_order_id) REFERENCES public.work_orders(id) ON DELETE CASCADE;


--
-- Name: work_order_technicians work_order_technicians_assigned_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_order_technicians
    ADD CONSTRAINT work_order_technicians_assigned_by_id_fkey FOREIGN KEY (assigned_by_id) REFERENCES public.users(id);


--
-- Name: work_order_technicians work_order_technicians_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_order_technicians
    ADD CONSTRAINT work_order_technicians_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: work_order_technicians work_order_technicians_work_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_order_technicians
    ADD CONSTRAINT work_order_technicians_work_order_id_fkey FOREIGN KEY (work_order_id) REFERENCES public.work_orders(id) ON DELETE CASCADE;


--
-- Name: work_orders work_orders_assigned_to_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT work_orders_assigned_to_id_fkey FOREIGN KEY (assigned_to_id) REFERENCES public.users(id);


--
-- Name: work_orders work_orders_format_from_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT work_orders_format_from_id_fkey FOREIGN KEY (format_from_id) REFERENCES public.formats(id);


--
-- Name: work_orders work_orders_format_to_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT work_orders_format_to_id_fkey FOREIGN KEY (format_to_id) REFERENCES public.formats(id);


--
-- Name: work_orders work_orders_line_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT work_orders_line_id_fkey FOREIGN KEY (line_id) REFERENCES public.lines(id);


--
-- Name: work_orders work_orders_machine_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT work_orders_machine_id_fkey FOREIGN KEY (machine_id) REFERENCES public.machines(id);


--
-- Name: work_orders work_orders_maintenance_request_origin_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT work_orders_maintenance_request_origin_id_fkey FOREIGN KEY (maintenance_request_origin_id) REFERENCES public.maintenance_requests(id);


--
-- Name: work_orders work_orders_section_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT work_orders_section_id_fkey FOREIGN KEY (section_id) REFERENCES public.sections(id);


--
-- Name: work_orders work_orders_source_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT work_orders_source_document_id_fkey FOREIGN KEY (source_document_id) REFERENCES public.documents(id);


--
-- PostgreSQL database dump complete
--

