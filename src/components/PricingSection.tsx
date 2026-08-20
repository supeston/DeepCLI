import React from 'react';
import { Check, Zap, Sparkles, Shield, Cpu, ArrowRight } from 'lucide-react';
import { ScrollReveal } from './ScrollReveal';

export const PricingSection: React.FC = () => {
  return (
    <section id="pricing" className="py-24 bg-white border-t border-slate-200 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <ScrollReveal direction="down">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#536DFE]/10 text-[#536DFE] text-xs font-semibold uppercase tracking-wider mb-4 border border-[#536DFE]/20">
              <Sparkles className="w-3.5 h-3.5" />
              <span>100% Free & Open Source</span>
            </div>
            <h2 className="text-3xl sm:text-5xl font-normal text-[#1F1F1F] tracking-tight mb-6">
              Zero Token Bills. <br />
              <span className="font-medium text-[#536DFE]">Flagship AI For Everyone.</span>
            </h2>
            <p className="text-lg text-[#5F6368] font-normal leading-relaxed">
              DeepX работает через интеллектуальную обёртку над инфраструктурой DeepSeek. 
              Она автоматически эмулирует клиентские сессии и выполняет бесплатные прямые запросы к флагманским моделям, 
              полностью обходя платные лимиты и ограничения официального API.
            </p>
          </ScrollReveal>
        </div>

        {/* Pricing & Architecture Grid */}
        <div className="grid lg:grid-cols-12 gap-8 items-stretch max-w-6xl mx-auto">
          {/* Main Free Tier Card */}
          <div className="lg:col-span-7">
            <ScrollReveal direction="up" delay={150}>
              <div className="deepx-card p-8 sm:p-10 h-full flex flex-col justify-between border-2 border-[#536DFE]/40 relative bg-gradient-to-b from-white via-white to-slate-50 shadow-xl">
                <div className="absolute top-6 right-6">
                  <span className="px-3 py-1 bg-[#536DFE] text-white text-xs font-bold rounded-full uppercase tracking-wider shadow-sm">
                    Unlimited
                  </span>
                </div>

                <div>
                  <div className="text-xs font-bold uppercase tracking-wider text-[#536DFE] mb-2">
                    Community Edition
                  </div>
                  <div className="flex items-baseline gap-2 mb-4">
                    <span className="text-5xl font-normal text-[#1F1F1F] tracking-tight">$0</span>
                    <span className="text-slate-500 font-medium">/ навсегда без подписок</span>
                  </div>
                  <p className="text-sm text-slate-600 mb-8 leading-relaxed">
                    Никаких платных токенов, скрытых платежей, привязки карт или лимитов на количество запросов в сутки.
                  </p>

                  <div className="space-y-4 mb-8">
                    {[
                      {
                        title: 'Бесплатный доступ к флагманам DeepSeek',
                        desc: 'Прямые запросы к DeepSeek-V3 и DeepSeek-R1 (DeepThink) на максимальной скорости.',
                      },
                      {
                        title: 'Умная эмуляция сессий',
                        desc: 'Обход платных ограничений API и лимитов на токены за счёт встроенного прокси-движка.',
                      },
                      {
                        title: 'Локальная безопасность & Zero-Telemetry',
                        desc: 'Исходный код и контекст вашего проекта не отправляются на сторонние серверы аналитики.',
                      },
                      {
                        title: 'Полная интеграция с Windows',
                        desc: 'Поддержка ConPTY терминала, фоновых процессов и работы с буфером обмена (Win+V).',
                      },
                    ].map((feature, idx) => (
                      <div key={idx} className="flex items-start gap-3.5">
                        <div className="w-5 h-5 rounded-full bg-[#536DFE]/10 flex items-center justify-center shrink-0 mt-0.5 text-[#536DFE]">
                          <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                        </div>
                        <div>
                          <div className="text-sm font-medium text-slate-900">{feature.title}</div>
                          <div className="text-xs text-slate-500 leading-relaxed">{feature.desc}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <button
                  onClick={() => document.getElementById('download')?.scrollIntoView({ behavior: 'smooth' })}
                  className="w-full google-btn-indigo py-3.5 text-sm font-semibold justify-center shadow-lg shadow-[#536DFE]/25 cursor-pointer"
                >
                  <span>Начать пользоваться бесплатно</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </ScrollReveal>
          </div>

          {/* Technical Explanations & Comparison Cards */}
          <div className="lg:col-span-5 flex flex-col justify-between gap-6">
            <ScrollReveal direction="up" delay={250}>
              <div className="deepx-card p-6 sm:p-8 bg-slate-50 border border-slate-200 hover:border-[#536DFE]/40 transition-all">
                <div className="w-10 h-10 rounded-xl bg-[#536DFE]/10 text-[#536DFE] flex items-center justify-center mb-4">
                  <Cpu className="w-5 h-5" />
                </div>
                <h3 className="text-base font-semibold text-slate-900 mb-2">
                  Как это работает под капотом?
                </h3>
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                  DeepX использует легковесный обратный шлюз к веб-эндпоинтам DeepSeek. Клиент эмулирует авторизованные сессии браузера, что позволяет отправлять неограниченное количество запросов в обход коммерческого API-биллинга.
                </p>
              </div>
            </ScrollReveal>

            <ScrollReveal direction="up" delay={350}>
              <div className="deepx-card p-6 sm:p-8 bg-slate-50 border border-slate-200 hover:border-[#536DFE]/40 transition-all">
                <div className="w-10 h-10 rounded-xl bg-[#536DFE]/10 text-[#536DFE] flex items-center justify-center mb-4">
                  <Shield className="w-5 h-5" />
                </div>
                <h3 className="text-base font-semibold text-slate-900 mb-2">
                  Никаких ключей и привязок карт
                </h3>
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                  Вам не нужно регистрировать платёжные реквизиты или пополнять баланс в долларах. Скачиваете репозиторий, запускаете CLI — и сразу начинаете работу с топовым кодинг-ассистентом.
                </p>
              </div>
            </ScrollReveal>

            <ScrollReveal direction="up" delay={450}>
              <div className="deepx-card p-6 sm:p-8 bg-slate-900 text-white border border-slate-800 shadow-xl">
                <div className="flex items-center gap-2 text-xs font-mono text-[#536DFE] font-bold uppercase tracking-wider mb-2">
                  <Zap className="w-4 h-4" />
                  <span>DeepSeek R1 + V3 Reasoning</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Полноценное древо рассуждений (DeepThink), разбор архитектуры и генерация кода без цензуры и задержек.
                </p>
              </div>
            </ScrollReveal>
          </div>
        </div>
      </div>
    </section>
  );
};
