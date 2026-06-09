import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";

const routes: RouteRecordRaw[] = [
    {
        path: '/',
        name: 'landing',
        component: () => import('@/features/landing/views/LandingView.vue'),
    },
    {
        path: '/grade',
        name: 'grading',
        component: () => import('@/features/grading/views/GradingView.vue'),
    },
    {
        path: '/onboarding',
        name: 'onboarding',
        component: () => import('@/features/onboarding/views/OnboardingView.vue'),
    },
    {
        path: '/behavior',
        name: 'behavior',
        component: () => import('@/features/behavior/views/BehaviorView.vue'),
    },
    {
        path: '/behavior/:ruleId',
        name: 'behavior-template',
        component: () => import('@/features/behavior/views/BehaviorView.vue'),
    },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

export default router