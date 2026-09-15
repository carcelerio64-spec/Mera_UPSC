package com.upscprep.app

/**
 * Production builds must use the real app/backend flow.
 * Keep this switch disabled; the demo-only screens remain available in source
 * for development reference but are not activated at runtime.
 */
object DemoMode {
    const val ENABLED = false
    const val TOKEN = "demo-test-mode"
}
