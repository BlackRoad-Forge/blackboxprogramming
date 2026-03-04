const { Router } = require('express');
const healthRoutes = require('./health');
const stripeRoutes = require('./stripe');

const router = Router();

router.use(healthRoutes);
router.use('/stripe', stripeRoutes);

module.exports = router;
